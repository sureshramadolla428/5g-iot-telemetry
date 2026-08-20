# KPI and measurement formulas

Single implementation: `shared/metrics/`. Simulator, consumer, tests, SQL views, and Grafana all consume those results. **Do not copy formulas** into dashboards.

## Modeled vs measured (enforced)

| Tag | Meaning | Examples |
|---|---|---|
| `source=modeled` | Computed from `config/radio_model.yaml` (link budget + channel). UERANSIM has **no PHY**. | RSRP, RSRQ, RSSI, SS-SINR, CQI, MCS, TBS, path loss, Doppler, L_UP, NTN C/N0, A2G two-ray |
| `source=measured` | Observed on the MQTT/app path or read-only OS counters | Echo RTT, RFC 3550 jitter, PDR/PLR, sequence gaps/dups/reorders, message rate, DB ingest lag, `/proc/net/dev` bytes |

Pydantic rejects PHY fields tagged `measured`. Grafana modeled panels include the visible note **modeled — not radio-measured**. Constant: `metrics.constants.MODELED_DISCLAIMER`.

A later SDR/srsRAN/COTS integration should implement `metrics.radio.base.RadioModel` and may then emit `source=measured` for true radio quantities. Until then, RF stays modeled.

## Constants (`constants.py`)

- \(c = 299792458\) m/s
- \(k = 1.380649 \times 10^{-23}\) J/K
- \(T_0 = 290\) K
- \(N_0 = -174\) dBm/Hz (conventional; \(k T_0\) is ≈ −173.98 dBm/Hz)
- \(R_E = 6371\) km, \(k_{\mathrm{eff}} = 4/3\)
- GEO altitude \(35786\) km (nadir one-way delay ≈ **119 ms**)
- Default LEO 550 km, MEO 20000 km (YAML)

## Conversions — never average in dB

- \(\mathrm{mW} = 10^{\mathrm{dBm}/10}\), \(\mathrm{dBm} = 10\log_{10}(\mathrm{mW})\)
- Power ratio: \(10^{x/10}\); amplitude: \(10^{x/20}\)
- `avg_db()`: convert to linear power, mean, convert back
- SQL: **forbidden** `AVG(rsrp_dbm)`. Use `dbm_from_mw(AVG(rsrp_mw))` / view `v_rsrp_avg`

## Noise / SNR / SINR / Eb/N0

- \(P_N = N_0 + 10\log_{10}(B) + NF\) dBm
- \(\mathrm{SNR} = P_{rx} - P_N\) dB
- \(\mathrm{SINR} = S / (I+N)\) (linear)
- \(E_b/N_0 = \mathrm{SNR} \cdot B/R\)
- Noise rise \((I+N)/N\)

## TS 38.215 / 38.133

- \(\mathrm{RSRQ} = N \cdot \mathrm{RSRP}/\mathrm{RSSI}\) (linear)
- Identity: \(\mathrm{RSRQ}_{dB} = \mathrm{RSRP}_{dBm} - \mathrm{RSSI}_{dBm} + 10\log_{10} N\)
- SS-RSRP report range −156…−31 dBm; SS-RSRQ −43…20 dB; SS-SINR −23…40 dB (quantized)

## Link budget and path loss

- \(\mathrm{EIRP} = P_{tx} + G_{tx} - L_{feeder}\)
- \(P_{rx} = \mathrm{EIRP} - PL + G_{rx} - L_{rx}\)
- FSPL three forms (m/Hz, km/GHz, km/MHz) in `pathloss.py`
- Log-distance: \(PL(d) = PL(d_0) + 10 n \log_{10}(d/d_0)\)
- **TR 38.901 UMa LOS** with \(d_{BP}' = 4 h_{BS}' h_{UT}' f_c / c\), \(h' = h-1\) m, PL1/PL2 exactly as Table 7.4.1-1

## CQI / MCS / TBS

- CQI tables 1/2/3 and MCS Table 5.1.3.1-1 are **data tuples**, not if-chains
- TBS: TS 38.214 §5.1.3.2 including Table 5.1.3.2-1
- **Approximation:** SINR→CQI picks the highest tabulated efficiency \(\le \log_2(1+\mathrm{SINR}_{\mathrm{lin}})\) (Shannon). 3GPP does not specify a unique mapping.

## HARQ

- Residual BLER \(= \mathrm{BLER}^{N_{tx}}\) (independent attempts)
- \(\mathrm{PER} = 1-(1-\mathrm{BLER})^{N_{TB}}\)

## Latency

- **Measured RTT:** MQTT `iot/devices/{id}/echo` ping/pong over the actual path
- **OWD:** `RTT/2` only if `clocks_synced: true`; else `null`
- Jitter: RFC 3550 \(J_i = J_{i-1} + (|D|-J_{i-1})/16\)
- PDV: RFC 3393 relative to min delay, p50/p95/p99
- Modeled \(L_{UP} = t_{proc}+t_{queue}+t_{tx}+t_{prop}+t_{HARQ}\); \(t_{prop}=d/c\) (NTN/A2G slant range when those models are on)
- Latency budget % = \(100 \cdot L / L_{budget}\)

## Goodput / PDR / rate

- Goodput = useful bits / time (headers excluded; see `OVERHEAD_STACK`)
- Interface throughput: read-only `/proc/net/dev` or `ip -s link`
- PDR from `sequence_number`; **gaps, duplicates, reorders counted separately**

## Mobility / HO

- Doppler \(f_d=(v/c) f \cos\theta\)
- \(T_c \approx 0.423 / f_{d,max}\); \(B_c \approx 1/(2\pi \sigma_\tau)\)
- SCS warning if \(|f_d| > 0.1 \times \mathrm{SCS}\)
- Haversine + bearing on GPS walk
- L3: \(a=2^{-k/4}\), \(F_n=(1-a)F_{n-1}+a M_n\) (TS 38.331)
- A3 entering: \(M_n+O_{fn}+O_{cn}-Hys > M_p+O_{fp}+O_{cp}+Off\)

## NTN (`enable_ntn: true` or `ENABLE_NTN_MODEL=true`)

Modeled only. Slant range, delays, orbit-speed Doppler, G/T, C/N0, rain/gas/scintillation losses. GEO nadir OWD ≈ 119 ms. Does **not** edit any NTN lab repo.

## A2G (`enable_a2g: true` or `ENABLE_A2G_MODEL=true`)

Modeled only. Radio horizon (refuse beyond unless `allow_beyond_horizon`), slant range, elevation, two-ray, Fresnel F1, aircraft Doppler: **peak positive on approach, zero overhead, negative on departure**. Truncation-driven assumptions are listed in `shared/metrics/a2g.py`. Does **not** edit any A2G lab repo.

## Enable flags

```yaml
# config/radio_model.yaml
profile: terrestrial   # default UMa-ish
enable_ntn: false
enable_a2g: false      # mutually exclusive with enable_ntn
```

Or environment: `ENABLE_NTN_MODEL=true` / `ENABLE_A2G_MODEL=true` when starting the host simulator.

## 3GPP references

TS 38.214, TS 38.215, TS 38.133, TS 38.331, TR 38.901, RFC 3550, RFC 3393.
