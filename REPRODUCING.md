# 复现说明

本页对应正式版本 1.0.0。使用 Python 3.12。除完整重建时主动下载原始包外，三层入口不联网获取研究数据。依赖安装本身需要软件包源或本地缓存。

每次运行将输出写到一个新目录，默认位于 `reproductions/时间戳-随机后缀/`。也可以传 `--output "一个尚不存在的目录"`。已有输出目录会被拒绝，不覆盖冻结结果。若某步失败，查看该次输出的 `validation.json` 和 `logs/`；修正原因后换一个新输出目录重跑。

## 1. 快速核查：不安装第三方库

在项目根目录执行：

```text
python reproduce.py
```

该入口使用 Python 标准库核验 `MANIFEST_SHA256.csv` 与原分析文件清单，检查 1094 行周期数据（两个窗口各 547 对），按时间块、质量条件和校准子集重算保存预测的全部评分，并检查已开放标签早于预测时点、各模型标签预算相同。

它核查的是保存结果的内部一致性，没有重新拟合模型或读取 2376 万行原始数据。

## 2. 从整理数据重跑全部分析

先创建独立环境并安装锁定依赖。Windows PowerShell：

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe reproduce.py --mode analysis
```

Linux/macOS：

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python reproduce.py --mode analysis
```

分析层使用随包的 `cycles.csv`、`characterization_tails.csv`、`gc_observations.csv` 和 `stages.csv`。它重新计算冻结模型、逐时点标签揭示模型、所有揭示偏移、分块比较、指数窗口敏感性、历史敏感性及汇总，再生成六张 PNG 和六张 SVG，执行 5 项因果时间检查。

提取阶段产生的指数剖面、周期表和历史原始审计在此模式中沿用冻结文件。只有下一层才重建这些内容。逐表比较会检查标签、行列数和数值；默认浮点容差为 `rtol=1e-9`、`atol=1e-12`，空值位置也要一致。图表会重画；SVG 中的时间元数据和元素 ID 不要求字节相同。

指数拟合的 R² 是一项限定例外：`cycles.csv`、`exponential_fits.csv` 与 `exponential_window_sensitivity.csv` 中的 `exp_r2` 使用绝对容差 `1e-8`。其展开的残差平方和在低方差窗口中会放大不同数学库的末位舍入差异；本次复现的最大 R² 差值约为 `1.19e-9`。拟合参数、预测、误差、布尔判断和其他列继续使用原规则。每次比对都记录这项例外的实际最大差值；7 项回归检查确保明显的 R² 错误、参数变化、缺失值和判断变化仍被拒绝。依据见 [数值可移植性记录](validation/numerical-portability.json)。

## 3. 从固定原始数据完整重建

依赖安装完成后，用虚拟环境中的 Python 运行：

```text
python reproduce.py --mode full --download
```

若没有激活虚拟环境，将上面的 `python` 替换为第 2 步的 `.venv` Python 路径。入口下载 [Zenodo 19361280](https://doi.org/10.5281/zenodo.19361280) 的固定 ZIP，核验 199357168 字节、官方 MD5 与本项目记录的 SHA-256，然后分块读取四个原始 CSV。完整重建建议预留 2 GB 磁盘空间；耗时取决于电脑。

已有原始 ZIP 时可全程离线：

```text
python reproduce.py --mode full --raw-archive "path/to/pem_water_electrolysis_degradation_data.zip"
```

完整模式在新的 `workspace/` 中重建 GC、OCV、操作段、周期、指数剖面，再执行第 2 层的分析。随后用另一套标准库实现从原始 ZIP 抽查 32 个高低载尾窗。所有随包 CSV/JSON 结果与重建结果逐项比较；OCV 明细由完整模式生成但不随轻量包分发。

## 时序检查与判断边界

安装依赖后，可单独执行 `python tests/test_reproduction.py`，运行上述 7 项数值比对回归检查。

已有的 5 项检查分别验证：隐藏低载标签不改变预测；当前校准标签不改变本轮预测；未来低载温压和时长不进入特征；已用标签在预测前结束；所有模型共享标签预算。这些检查针对算法的时间可用性，不构成新的实验验证。

主时间切分使用 `time_h`（高载末次 GC），而 `forecast_h` 是高载电气操作段终点。原方案按随后低载终点切分得到 28 个 Pt/C 训练周期，主分析用高载时间得到 27 个，二者分别保留。

## 环境与维护

`requirements.txt` 锁定本次使用的数值与绘图库及其依赖。`00_admin/environment.json` 是历史研究环境，包含报告制作等额外库；不应直接照抄为最小运行环境。

本次实际通过的平台、运行范围和结果见 [VALIDATION.md](VALIDATION.md)。Windows/Ubuntu 的 GitHub Actions 实际运行状态见 [Actions](https://github.com/SHIN09-git/pem-load-transfer-audit/actions)；本页不以配置文件的存在代替运行结果。

如改变模型、数据或参数，应重新生成并审阅结果和报告；不要只重算散列后继续使用旧结论。完整 ZIP 和生成结果在 `.gitignore` 中排除，避免意外加入未来公开提交。

