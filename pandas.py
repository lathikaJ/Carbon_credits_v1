"""
Lightweight pure-Python fallback shim for pandas.
Provides basic DataFrame, Series, read_csv, merge, isna, and notna when pandas is not installed.
"""

from typing import Dict, List, Any, Optional, Union, Iterator, Tuple
import csv


def isna(val: Any) -> bool:
    if val is None:
        return True
    s = str(val).strip().lower()
    return s in ("nan", "none", "null", "")


def notna(val: Any) -> bool:
    return not isna(val)


class Series:
    def __init__(self, data: List[Any], name: Optional[str] = None):
        self._data = list(data)
        self.name = name

    @property
    def empty(self) -> bool:
        return len(self._data) == 0

    def sum(self) -> float:
        return sum(float(x) for x in self._data if not isna(x))

    def mean(self) -> float:
        valid = [float(x) for x in self._data if not isna(x)]
        return sum(valid) / len(valid) if valid else 0.0

    def min(self) -> float:
        valid = [float(x) for x in self._data if not isna(x)]
        return min(valid) if valid else 0.0

    def max(self) -> float:
        valid = [float(x) for x in self._data if not isna(x)]
        return max(valid) if valid else 0.0

    def unique(self) -> List[Any]:
        return list(dict.fromkeys(self._data))

    def fillna(self, value: Any) -> 'Series':
        new_data = [value if isna(x) else x for x in self._data]
        return Series(new_data, name=self.name)

    def astype(self, dtype: Any) -> 'Series':
        new_data = []
        for x in self._data:
            if isna(x):
                new_data.append(dtype(0))
            else:
                try:
                    new_data.append(dtype(x))
                except (ValueError, TypeError):
                    new_data.append(dtype(0))
        return Series(new_data, name=self.name)

    def __eq__(self, other: Any) -> 'Series':  # type: ignore[override]
        if isinstance(other, Series):
            return Series([a == b for a, b in zip(self._data, other._data)])
        return Series([a == other for a in self._data])

    def __ne__(self, other: Any) -> 'Series':  # type: ignore[override]
        if isinstance(other, Series):
            return Series([a != b for a, b in zip(self._data, other._data)])
        return Series([a != other for a in self._data])

    def __gt__(self, other: Any) -> 'Series':
        return Series([(float(x) > float(other) if not isna(x) else False) for x in self._data])

    def __ge__(self, other: Any) -> 'Series':
        return Series([(float(x) >= float(other) if not isna(x) else False) for x in self._data])

    def __lt__(self, other: Any) -> 'Series':
        return Series([(float(x) < float(other) if not isna(x) else False) for x in self._data])

    def __le__(self, other: Any) -> 'Series':
        return Series([(float(x) <= float(other) if not isna(x) else False) for x in self._data])

    @property
    def iloc(self) -> Any:
        class ILocSeries:
            def __init__(self, s):
                self.s = s
            def __getitem__(self, idx):
                return self.s._data[idx]
        return ILocSeries(self)

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def tolist(self):
        return list(self._data)


class GroupBy:
    def __init__(self, groups: Dict[Any, List[Dict[str, Any]]]):
        self._groups = groups

    def __iter__(self) -> Iterator[Tuple[Any, 'DataFrame']]:
        for key, rows in self._groups.items():
            yield key, DataFrame(rows)


class DataFrame:
    def __init__(self, data: Union[List[Dict[str, Any]], Dict[str, List[Any]], None] = None):
        if data is None:
            self._records = []
        elif isinstance(data, list):
            self._records = [dict(r) for r in data]
        elif isinstance(data, dict):
            keys = list(data.keys())
            length = len(data[keys[0]]) if keys else 0
            self._records = [{k: data[k][i] for k in keys} for i in range(length)]
        else:
            self._records = []

    @property
    def empty(self) -> bool:
        return len(self._records) == 0

    @property
    def columns(self) -> List[str]:
        if not self._records:
            return []
        cols = []
        for r in self._records:
            for k in r.keys():
                if k not in cols:
                    cols.append(k)
        return cols

    def __len__(self) -> int:
        return len(self._records)

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, str):
            vals = [r.get(key) for r in self._records]
            return Series(vals, name=key)
        elif isinstance(key, list):
            return DataFrame([{k: r.get(k) for k in key} for r in self._records])
        elif isinstance(key, Series):
            return DataFrame([r for r, keep in zip(self._records, key._data) if keep])
        raise KeyError(key)

    def __setitem__(self, key: str, value: Any):
        if isinstance(value, (list, Series)):
            val_list = list(value)
            for i, r in enumerate(self._records):
                r[key] = val_list[i] if i < len(val_list) else None
        else:
            for r in self._records:
                r[key] = value

    @property
    def iloc(self) -> Any:
        class ILocDF:
            def __init__(self, df):
                self.df = df
            def __getitem__(self, idx):
                if isinstance(idx, int):
                    return self.df._records[idx]
                return DataFrame(self.df._records[idx])
        return ILocDF(self)

    def groupby(self, by: str) -> GroupBy:
        groups: Dict[Any, List[Dict[str, Any]]] = {}
        for r in self._records:
            val = r.get(by)
            groups.setdefault(val, []).append(r)
        return GroupBy(groups)

    def iterrows(self) -> Iterator[Tuple[int, Dict[str, Any]]]:
        for idx, r in enumerate(self._records):
            yield idx, r

    def to_dict(self, orient: str = "records") -> Any:
        if orient == "records":
            return [dict(r) for r in self._records]
        return self._records

    def fillna(self, value: Any) -> 'DataFrame':
        new_records = []
        for r in self._records:
            new_r = {}
            for k, v in r.items():
                new_r[k] = value if isna(v) else v
            new_records.append(new_r)
        return DataFrame(new_records)

    def isna(self) -> 'DataFrame':
        new_records = []
        for r in self._records:
            new_records.append({k: isna(v) for k, v in r.items()})
        return DataFrame(new_records)


def read_csv(filepath: str, **kwargs) -> DataFrame:
    records = []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            parsed_row = {}
            for k, v in row.items():
                if v is None or v == "":
                    parsed_row[k] = None
                else:
                    try:
                        parsed_row[k] = float(v) if "." in v or "e" in v.lower() else int(v)
                    except ValueError:
                        parsed_row[k] = v
            records.append(parsed_row)
    return DataFrame(records)


def merge(
    left: DataFrame,
    right: DataFrame,
    on: Union[str, List[str]],
    how: str = "inner",
    suffixes: Tuple[str, str] = ("_x", "_y"),
) -> DataFrame:
    on_keys = [on] if isinstance(on, str) else list(on)
    right_map: Dict[Tuple[Any, ...], List[Dict[str, Any]]] = {}
    for r in right._records:
        key = tuple(str(r.get(k)) for k in on_keys)
        right_map.setdefault(key, []).append(r)

    merged_records = []
    matched_right_keys = set()

    for l in left._records:
        key = tuple(str(l.get(k)) for k in on_keys)
        matches = right_map.get(key, [])
        if matches:
            matched_right_keys.add(key)
            for m in matches:
                merged_row = dict(l)
                for k, v in m.items():
                    if k in on_keys:
                        continue
                    if k in merged_row:
                        suf_l, suf_r = suffixes
                        merged_row[f"{k}{suf_l}"] = merged_row.pop(k)
                        merged_row[f"{k}{suf_r}"] = v
                    else:
                        merged_row[k] = v
                merged_records.append(merged_row)
        else:
            if how in ("left", "outer"):
                merged_records.append(dict(l))

    if how in ("right", "outer"):
        for key, matches in right_map.items():
            if key not in matched_right_keys:
                for m in matches:
                    merged_records.append(dict(m))

    return DataFrame(merged_records)
