from typing import Optional, Dict, Iterable
import numpy as np
from ..metrics import mae, rmse


# ============== NEO (Nonlinear Evolution Operator) ==============
class NEOForecaster:
    """
    Nonlinear Evolution Operator (NEO) forecaster with polynomial features over lags.

    Parameters
    ----------
    lags : int, default=5
        Number of autoregressive lags to use.
    degree : int, default=2
        Polynomial degree of the feature expansion (1 = linear, 2 = quadratic, etc.).
    window_size : int or None, default=None
        Rolling window size for fitting. If ``None``, all available training data is used.

    Attributes
    ----------
    coef_ : ndarray of shape (n_features,), optional
        Learned coefficients from least squares fitting.
    last_window_ : ndarray of shape (lags,), optional
        Last observed lag window from training, stored for iterative prediction.
    """

    def __init__(self, lags: int = 5, degree: int = 2, window_size: Optional[int] = None):
        self.lags = int(lags)
        self.degree = int(degree)
        self.window_size = window_size
        self.coef_: Optional[np.ndarray] = None
        self.last_window_: Optional[np.ndarray] = None

        # --- Internal stabilization state (doesn't change public API) ---
        self._mu_: Optional[float] = None
        self._sigma_: Optional[float] = None
        self._last_window_std_: Optional[np.ndarray] = None
        self._ridge_alpha: float = 1e-6  # tiny ridge to tame collinearity

    def _features(self, state: np.ndarray) -> np.ndarray:
        """
        Construct polynomial features from a lag state vector.

        Parameters
        ----------
        state : ndarray of shape (lags,)
            Lagged values with the newest observation first.

        Returns
        -------
        feats : ndarray of shape (n_features,)
            Expanded feature vector including polynomial terms up to `degree`.
        """
        feats = [1.0]
        n = len(state)
        feats.extend(state.tolist())

        if self.degree >= 2:
            for i in range(n):
                si = state[i]
                for j in range(i, n):
                    feats.append(si * state[j])

        if self.degree >= 3:
            for i in range(n):
                si = state[i]
                for j in range(i, n):
                    sij = si * state[j]
                    for k in range(j, n):
                        feats.append(sij * state[k])

        return np.array(feats, dtype=float)

    # ---- Internal helpers for scaling (private, no API/docstring changes) ----
    def _standardize_fit(self, y: np.ndarray) -> np.ndarray:
        mu = float(np.mean(y))
        sigma = float(np.std(y, ddof=0))
        if not np.isfinite(sigma) or sigma == 0.0:
            sigma = 1.0
        self._mu_, self._sigma_ = mu, sigma
        return (y - mu) / sigma

    def _standardize_apply(self, y: np.ndarray) -> np.ndarray:
        return (y - self._mu_) / self._sigma_

    def _destandardize(self, z: np.ndarray) -> np.ndarray:
        return z * self._sigma_ + self._mu_

    def fit(self, y: np.ndarray) -> "NEOForecaster":
        """
        Fit the NEO forecaster to a univariate time series.

        Parameters
        ----------
        y : array_like of shape (n_samples,)
            Univariate training series.

        Returns
        -------
        self : NEOForecaster
            The fitted model instance.

        Raises
        ------
        ValueError
            If the series is too short for the chosen lag length.
        """
        y = np.asarray(y, float)
        if not np.isfinite(y).all():
            raise ValueError("Input y contains NaN or Inf.")
        N = len(y)
        m = self.lags
        if N < m + 1:
            raise ValueError(f"Need at least {m+1} points, got {N}.")
        start = 0 if (self.window_size is None or self.window_size >= N) else (N - self.window_size)
        start = max(start, m - 1)

        # Standardize target to keep polynomial products bounded
        z = self._standardize_fit(y)

        X_rows = []
        targets = []
        for t in range(start, N - 1):
            state = z[t - m + 1 : t + 1][::-1]  # newest first
            X_rows.append(self._features(state))
            targets.append(z[t + 1])
        X = np.vstack(X_rows).astype(np.float64, copy=False)
        Y = np.array(targets, dtype=np.float64)

        # Ridge-regularized normal equations: (X^T X + αI) w = X^T Y
        XT = X.T
        A = XT @ X
        # add tiny ridge to diagonal to avoid blow-ups / singularities
        A.flat[:: A.shape[0] + 1] += self._ridge_alpha
        b = XT @ Y
        w = np.linalg.solve(A, b)

        self.coef_ = w
        self.last_window_ = y[-m:].copy()         # original scale (for external use)
        self._last_window_std_ = z[-m:].copy()    # standardized window (for internal prediction loop)
        return self

    def predict(self, h: int, start_values: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Generate iterative forecasts.

        Parameters
        ----------
        h : int
            Forecast horizon (number of steps ahead).
        start_values : ndarray of shape (lags,), optional
            Initial lag window. If ``None``, uses the training window.

        Returns
        -------
        fcst : ndarray of shape (h,)
            Forecasted values.

        Raises
        ------
        RuntimeError
            If the model is not yet fitted or no valid starting window is available.
        ValueError
            If `start_values` has incorrect length.
        """
        if self.coef_ is None:
            raise RuntimeError("Fit the model before predicting.")
        if self._mu_ is None or self._sigma_ is None:
            raise RuntimeError("Model scaling parameters not set. Fit the model before predicting.")

        m = self.lags

        # Build the starting window in STANDARDIZED space
        if start_values is None:
            if self._last_window_std_ is None:
                raise RuntimeError("No start_values and no training window available.")
            window_std = self._last_window_std_.copy()
        else:
            start_values = np.asarray(start_values, float)
            if len(start_values) != m:
                raise ValueError(f"start_values must have length {m}.")
            window_std = self._standardize_apply(start_values)

        fcst_std = []
        for _ in range(h):
            state_std = window_std[::-1]
            phi = self._features(state_std)
            zhat = float(np.dot(self.coef_, phi))
            fcst_std.append(zhat)
            window_std[:-1] = window_std[1:]
            window_std[-1] = zhat

        # De-standardize forecasts back to original scale
        return self._destandardize(np.array(fcst_std, dtype=np.float64))


class AutoNEO:
    """
    Automatic hyperparameter tuner for :class:`NEOForecaster`.

    This class performs a grid search over lag length, polynomial degree,
    and optional rolling window size fractions. A holdout validation set
    is taken from the end of the input series, candidate models are fit
    on the training segment, and scored on the validation block. The best
    configuration is then refit on the entire series.

    Parameters
    ----------
    lags_grid : iterable of int, default=(4, 8, 12)
        Candidate autoregressive lag lengths to evaluate.
    degree_grid : iterable of int, default=(1, 2, 3)
        Candidate polynomial degrees for the forecaster.
    window_fracs : iterable of {float, None}, default=(None, 0.5, 0.75)
        Fractions of the training set length to use for rolling windows.
        If ``None``, all available training data is used.
        If float ``w`` in (0, 1], window size is computed as
        ``max(lags + 8, int(len(y_train) * w))``.

    Attributes
    ----------
    model_ : NEOForecaster or None
        The final fitted forecaster using the best-found configuration.
    best_ : dict or None
        Dictionary with keys:
            - ``"config"`` : dict of best hyperparameters
            - ``"val_score"`` : float validation score
        Populated after :meth:`fit`.
    """

    def __init__(
        self,
        lags_grid: Iterable[int] = (4, 8, 12),
        degree_grid: Iterable[int] = (1, 2, 3),
        window_fracs: Iterable[Optional[float]] = (None, 0.5, 0.75),
    ):
        self.lags_grid = lags_grid
        self.degree_grid = degree_grid
        self.window_fracs = window_fracs
        self.model_: Optional[NEOForecaster] = None
        self.best_: Optional[Dict] = None

    def fit(self, y: np.ndarray, val_fraction: float = 0.25, metric: str = "mae") -> "AutoNEO":
        """
        Fit the auto-tuner on a univariate time series.

        Parameters
        ----------
        y : array_like of shape (n_samples,)
            Univariate time series data.
        val_fraction : float, default=0.25
            Fraction of samples reserved for validation. The actual size is
            ``max(16, int(n_samples * val_fraction))`` to ensure at least 16
            validation points.
        metric : {"mae", "rmse"}, default="mae"
            Scoring metric used for validation selection.

        Returns
        -------
        self : AutoNEO
            The fitted instance with :attr:`model_` and :attr:`best_` set.
        """
        y = np.asarray(y, float)
        N = len(y)
        n_val = max(16, int(N * val_fraction))
        split = N - n_val
        y_train = y[:split]
        y_val = y[split:]

        best_score = np.inf
        best_model = None
        best_conf = None

        for lags in self.lags_grid:
            for degree in self.degree_grid:
                for wfrac in self.window_fracs:
                    window_size = None
                    if wfrac is not None:
                        window_size = max(lags + 8, int(len(y_train) * float(wfrac)))
                    try:
                        neo = NEOForecaster(lags=lags, degree=degree, window_size=window_size)
                        neo.fit(y_train)
                        start_vals = y_train[-lags:]
                        preds = neo.predict(len(y_val), start_values=start_vals)
                        score = mae(y_val, preds) if metric == "mae" else rmse(y_val, preds)
                        if score < best_score:
                            best_score = score
                            best_model = neo
                            best_conf = dict(lags=lags, degree=degree, window_size=window_size)
                    except Exception:
                        continue

        final = NEOForecaster(**best_conf)
        final.fit(y)
        self.model_ = final
        self.best_ = dict(config=best_conf, val_score=best_score)
        return self

    def predict(self, h: int):
        """
        Generate forecasts using the best-fitted model.

        Parameters
        ----------
        h : int
            Forecast horizon, i.e., number of future steps to predict.

        Returns
        -------
        y_pred : ndarray of shape (h,)
            Forecasted values.
        """
        return self.model_.predict(h)
