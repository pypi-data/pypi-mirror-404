from io import BytesIO
from typing import Union, Callable, Any

import pandas as pd

from .dataset import PhysicalDataManage

class ContinuousOptimizer:
    def __init__(
        self,
        fh: Union[str, BytesIO],
        dm: PhysicalDataManage,
        lTerm: Callable[..., Any],
        mTerm: Callable[..., Any],
    ) -> None: ...
    def fit(self, epochs: int) -> None: ...
    def export(self, fh: Union[str, BytesIO]) -> None: ...
    def steps(self, df: pd.DataFrame) -> pd.DataFrame: ...
    def plots(self, df: pd.DataFrame) -> None: ...
