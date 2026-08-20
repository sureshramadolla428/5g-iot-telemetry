"""Physical constants for modeled radio KPIs. Not used as measured PHY."""

from __future__ import annotations

# Speed of light (m/s), CODATA.
C_MPS = 299_792_458.0

# Boltzmann (J/K), CODATA 2019 exact.
K_BOLTZMANN = 1.380649e-23

# Reference noise temperature (K).
T0_K = 290.0

# Thermal noise spectral density: 10*log10(k*T0 * 1000) dBm/Hz ≈ -173.98, rounded to
# the conventional link-budget value -174 dBm/Hz.
N0_DBM_PER_HZ = -174.0

# Mean Earth radius (km) used in radio-horizon / NTN geometry.
R_E_KM = 6371.0
R_E_M = R_E_KM * 1000.0

# Effective-Earth-radius factor (4/3).
K_FACTOR = 4.0 / 3.0

# Geostationary altitude above mean sea level (km). One-way nadir delay ≈ 119 ms.
GEO_ALTITUDE_KM = 35786.0

# Default circular-orbit altitudes when NTN profile is enabled (km).
LEO_ALTITUDE_KM_DEFAULT = 550.0
MEO_ALTITUDE_KM_DEFAULT = 20000.0

# Visible disclaimer required on every modeled radio KPI surface.
MODELED_DISCLAIMER = "modeled — not radio-measured"
SOURCE_MODELED = "modeled"
SOURCE_MEASURED = "measured"

SCHEMA_VERSION = "1.1.0"
