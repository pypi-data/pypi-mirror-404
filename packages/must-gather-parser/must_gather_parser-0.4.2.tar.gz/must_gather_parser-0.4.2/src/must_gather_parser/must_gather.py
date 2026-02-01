import logging
import os
import re
import asyncio
import json
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ProcessPoolExecutor
from itertools import chain
from importlib import resources
from typing import List, AsyncIterator, Any

import aiofiles
import yaml
try:
    from yaml import CSafeLoader as BaseSafeLoader
except:
    from yaml import SafeLoader as BaseSafeLoader


logger = logging.getLogger(__name__)

must_gather_timestamp_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)\s+([+-]\d{4})")


class ResourceNotFound(Exception):
    pass


def parse_k8s_file_as_list(f):
    with open(f, 'rb') as file:
        unstruct = yaml.load(file, Loader=K8sSafeLoader)
    if "items" in unstruct:
        return unstruct
    return {"apiVersion": "v1", "kind": "List", "items": [unstruct]}


def parse_crd_file(f):
    with open(f, 'rb') as file:
        return yaml.load(file, Loader=K8sSafeLoader)


class K8sSafeLoader(BaseSafeLoader):
    """Custom loader for K8s manifests with special handling."""
    pass


def construct_undefined(loader, node):
    """Treat undefined tags as strings."""
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    elif isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    elif isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)


K8sSafeLoader.add_constructor(None, construct_undefined)


def parse_log_datetime(line: str) -> datetime:
    match = must_gather_timestamp_pattern.match(line)
    if not match:
        return None
    timestamp_str, offset_str = match.groups()

    # --- Normalize second's fractions up to 6 chars ---
    # es: "2025-06-29 06:41:53.304214614" -> "2025-06-29 06:41:53.304214"
    if '.' in timestamp_str:
        base, frac = timestamp_str.split('.')
        frac = (frac + "000000")[:6] 
        timestamp_str = f"{base}.{frac}"

    dt = datetime.strptime(timestamp_str + offset_str, "%Y-%m-%d %H:%M:%S.%f%z")
    return dt.astimezone(timezone.utc)


class MustGather:
    def __init__(self):
        self.path = None
        self.root_dirs = {}
        self.timestamp = None
        self.crds = {}
        self.api_resources = {}
        self.executor = ProcessPoolExecutor(
            max_workers=min(os.cpu_count() or 4, 16)
        )
        self.semaphore = asyncio.Semaphore(min(os.cpu_count() or 4, 16))



    def _get_cpu_limit(self, default=1):
        try:
            with open("/sys/fs/cgroup/cpu.max") as f:
                quota, period = f.read().strip().split()
                if quota != "max":
                    return max(1, int(int(quota) / int(period)))
        except Exception:
            pass
        return default


    async def use(self, path):
        self.path = Path(path).expanduser()
        self.root_dirs = self._root_dirs()
        if not self.path.exists():
            raise FileNotFoundError(f'{self.path} does not exist')
        
        if not self.root_dirs:
            raise ValueError(f'Invalid must-gather: no "timestamp" file found in {self.path} subdirectories')
        self.api_resources = await self._api_resources()


    def close(self):
        if self.executor is not None:
            self.executor.shutdown(wait=True)


    def _root_dirs(self):
        root_dirs = {}
        for path in self.path.rglob("timestamp"):
            root_dirs[path.parent.absolute().as_posix()] = {"timestamp" : self._get_must_gather_timestamp(path)}
        if len(root_dirs) > 1:
            root_dirs_list= list(root_dirs.keys())
            if root_dirs_list[0] in root_dirs_list[1]:
                root_dirs.pop(root_dirs_list[0], None)
        if root_dirs:
            self.timestamp = min([v["timestamp"] for v in root_dirs.values()]) 
        return root_dirs


    def _get_must_gather_timestamp(self, timestamp_path):
        with open(timestamp_path, 'r', encoding='utf-8') as timestamp_file_open:
            return parse_log_datetime(timestamp_file_open.readline().strip())
    

    def _collect_crds(self):
        crd_files = chain.from_iterable(
            (Path(must_gather) / "cluster-scoped-resources" / "apiextensions.k8s.io" / "customresourcedefinitions").glob('*.yaml') 
            for must_gather in self.root_dirs.keys()
        )
        results = self.executor.map(parse_crd_file, crd_files)
        for crd in results:
            crd_group = crd.get("spec", {}).get("group", "")
            if crd_group not in self.crds:
                self.crds[crd.get("spec", {}).get("group", "")] = {}
            plural_name = crd.get("spec", {}).get("names", {}).get("plural", "")
            self.crds[crd_group][plural_name] = {"namespaced": crd.get("spec", {}).get("scope") == "Namespaced"}
    

    def _get_resource_paths(self, resource_kind_plural, group, namespace, all_namespaces, namespaced):
        group = "core" if group in {"", "v1"} else group
        sub_folder = "namespaces" if namespaced else "cluster-scoped-resources"
        path = "" if not namespaced else ("*/" if (all_namespaces or not namespace) else f"{namespace}/")  
        logging.debug(f'checking for resources into: "<MUST_GATHER>/{sub_folder}/{path}{group}/{resource_kind_plural}/*"')
        resource_paths = list(chain.from_iterable(
            (Path(f'{must_gather}/{sub_folder}')).glob(f'{path}{group}/{resource_kind_plural}/*') 
            for must_gather in self.root_dirs.keys()
        ))
        # pods exception 
        if resource_kind_plural=="pods" and group=="core" and (len(self.root_dirs) > 1 or (len(self.root_dirs) == 1 and not resource_paths)):
                logging.debug(f'checking for resources into: "<MUST_GATHER>/{sub_folder}/{path}{resource_kind_plural}/*/*.yaml"')
                resource_paths.extend(list(chain.from_iterable(
                    (Path(f'{must_gather}/{sub_folder}')).glob(f'{path}{resource_kind_plural}/*/*.yaml') 
                    for must_gather in self.root_dirs.keys()
                )))
        
        if not resource_paths:
            logging.debug(f'checking for resources into: "<MUST_GATHER>/{sub_folder}/{path}{group}/{resource_kind_plural}.yaml"')
            resource_paths = list(chain.from_iterable(
                (Path(f'{must_gather}/{sub_folder}')).glob(f'{path}{group}/{resource_kind_plural}.yaml') 
                for must_gather in self.root_dirs.keys()
            ))

        return resource_paths


    async def get_resources(self, resource_kind_plural: str, group: str, namespace: str | None = "default", resource_name: List[str] = [], all_namespaces: bool | None = False, **kwargs):
        group = "v1" if group in {"", "core"} else group
        if (namespaced:=kwargs.get("namespaced")) is None or not isinstance(namespaced, bool):
            namespaced = self.api_resources.get(group, {}).get(resource_kind_plural, {}).get("namespaced", None)
        resource_paths = self._get_resource_paths(resource_kind_plural, group, namespace, all_namespaces, namespaced)
        loop = asyncio.get_running_loop()
        async with self.semaphore:
            tasks = [
                loop.run_in_executor(self.executor, parse_k8s_file_as_list, path)
                for path in resource_paths if not (path.name.startswith(".") or path.parent.name.startswith("."))

            ]
            results = await asyncio.gather(*tasks)
        uid_map = set()
        logging.debug(f"found {len(results)} results before applying deduplication")
        resulting_resources = [
            resource
            for items in results
            for resource in items.get("items", [])
            if (uid := resource.get("metadata", {}).get("uid")) not in uid_map
            and (not resource_name or resource.get("metadata", {}).get("name", "") in resource_name) and not uid_map.add(uid)
        ]
        if len(resource_name) == 1:
            if resulting_resources:
                return resulting_resources[0]
            raise ResourceNotFound
        return {"apiVersion": "v1", "kind": "List", "items": resulting_resources}
    

    async def _api_resources(self, skip_empty=True):
        api_resources = {}
    
        async def empty_items(file_path: Path):
            async with aiofiles.open(file_path, encoding="utf-8") as f:
                chunk = await f.read(512)
                for line in chunk.split("\n"):
                    if line.strip() == "items: []":
                        return True
            return False

        async def add_resource(resource_plural_path: Path, namespaced: bool):
            api_group = "v1" if resource_plural_path.parent.name == "core" else resource_plural_path.parent.name
            resource_plural = resource_plural_path.stem
            if api_group == "pods":
                api_resources.setdefault("v1", {}).setdefault(
                    "pods",
                    {"namespaced": namespaced},
                )
                return
            if skip_empty:
                if api_resources.get(api_group, {}).get(resource_plural) is not None:
                    return
                if resource_plural_path.is_file():
                    if await empty_items(resource_plural_path):
                        return 
                if resource_plural_path.is_dir():
                    if ( resource_plural_path / f"{resource_plural}.yaml" ).exists():
                        if await empty_items(resource_plural_path / f"{resource_plural}.yaml"):
                            return 
                    else:
                        if not any(resource_plural_path.iterdir()):
                            return             
            api_resources.setdefault(api_group, {}).setdefault(
                resource_plural,
                {"namespaced": namespaced},
            )
    
        for resource_plural_path in chain.from_iterable(
            Path(must_gather, "cluster-scoped-resources").glob("*/*")
            for must_gather in self.root_dirs
        ):
            if (
                resource_plural_path.name.startswith(".")
                or resource_plural_path.parent.name.startswith(".")
            ):
                continue
            await add_resource(resource_plural_path, namespaced=False)
    
        for resource_plural_path in chain.from_iterable(
            Path(must_gather, "namespaces").glob("*/*/*")
            for must_gather in self.root_dirs
        ):
            if (
                resource_plural_path.name.startswith(".")
                or resource_plural_path.parent.name.startswith(".")
            ):
                continue
            await add_resource(resource_plural_path, namespaced=True)
    
        return api_resources


    async def logs_pod(self, namespace, pod_name, container_name, fallback_to_previous=True) -> AsyncIterator[str]:
        container_previous_log_file = None
        container_log_file = None
        tail = ""
        log_files = chain.from_iterable(
                (Path(f'{must_gather}/namespaces/{namespace}/pods/{pod_name}/{container_name}/{container_name}/logs')).glob('*.log') 
                for must_gather in self.root_dirs.keys()
            )
        for log_file in log_files:
            if log_file.name == "current.log" and log_file.stat().st_size > 0:
                container_log_file = log_file
                break
            if fallback_to_previous and log_file.name == "previous.log" and log_file.stat().st_size > 0 and container_previous_log_file is None:
                container_previous_log_file = log_file

        container_log_file = container_log_file or container_previous_log_file
        if not container_log_file:
            return 
        if container_log_file:
            async with aiofiles.open(container_log_file, encoding="utf-8") as f:
                while chunk := await f.read(64 * 1024):
                    lines = (tail + chunk).split("\n")
                    tail = lines[-1]
                    for line in lines[:-1]:
                        yield line
                if tail:
                    yield tail
