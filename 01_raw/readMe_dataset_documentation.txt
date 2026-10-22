PAGE 1
Dataset documentation:
Time-Resolved Performance and Stability of Different Gas Recombination
Catalysts in PEM Water Electrolysis
Steffen Brundiersa, Patrick Trinkea, Simon Geigerb, Victor-Alfonso Gracia-Medrano-Bravob, Marek Hubkab, Jan
Ilsemannb, Boris Bensmanna,∗, Richard Hanke-Rauschenbacha
aLeibniz University Hannover , Institute of Electric Power Systems, 30167, Hannover , Germany
bQuest One GmbH, 22143, Hamburg, Germany
Contents
1 License and citation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .2
2 General Information . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 2
3 Dataset Table Description . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 2
4 Limitation and Additional Information . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 5
∗Corresponding author
Email address: boris.bensmann@ifes.uni-hannover.de (Boris Bensmann)

PAGE 2
1. License and Citation
The dataset is freely available under the Creative Commons Attribution 4.0 International (CC BY 4.0) license.
Users are kindly asked to cite the publication describing the measurement data, which is linked in the corresponding
Zenodo entry.
2. General Information
This documentation describes a dataset comprising electrochemical measurements and online gas analysis from
four polymer electrolyte membrane water electrolysis (PEMWE) single-cell long-term experiments, each with a du-
ration of approximately 1,500 hours. The investigated configurations include a reference cell (without recombination
catalyst) and cells equipped with di fferent gas recombination catalysts (PtNano, PtBlack, and Pt /C). For detailed in-
formation on materials, experimental methods, and interpretation of the measurement results, the reader is referred to
the original publication linked in the corresponding Zenodo entry. The dataset is intended to support further analysis,
including data-driven approaches such as machine learning, as well as physics-based modeling.
A general overview of the cell components and operating parameters is provided in Table 1 and Table 2, respec-
tively. Additional details can be found in the corresponding publication and its Supplementary Information document.
To facilitate data usage, a Jupyter notebook is provided among the uploaded files that demonstrates an example of
exploratory data analysis, enabling users to quickly familiarize themselves with the dataset.
Table 1: Overview of the parameters of the used electrolysis cell and materials.
cell parameter information
anode PTL Bekaert 1 mm Ti fiber, 50 nm sputter coated Ir
cathode GDL Freudenberg E20H, 210 µm carbon paper
CCMs 4x Quest One based on Nafion N115
electrolysis cell IfES-cell (in-house built), 4 cm 2 cell area
end plates Au plated Ti with parallel flow field
compression 2.37 kN
Table 2: Overview of the operating and test bench parameters.
operating parameter information
anode pressure ambient
cathode pressure 30 bar absolute
water temperature 80 ◦C
water flow rate 80 ml min −1
potentiostat BCS-815, BioLogic
gas chromatograph 990 microGC, Agilent
3. Dataset Table Description
The dataset is provided as four separate CSV files, each representing a distinct sample, while all files share an iden-
tical structure. The column names and their corresponding descriptions are summarized in Table 3. Columns related
to cell performance include time, applied electrical current, and cell voltage. Electrochemical impedance spectroscopy
(EIS) data comprise the frequencies of the measurement points, as well as the corresponding impedance magnitude
and phase angle of the cell. In addition, the dataset contains information on the conductivity of the circulating water,
cathode pressure, and cell temperature, the latter measured within the flow field block using a Pt100 sensor.
Gas analysis data are provided both as raw measurements and as dilution-corrected values of the hydrogen con-
centration in oxygen (H2 in O2). This dilution is required for safety reasons and to ensure a minimum gas flow rate for
reliable gas chromatograph (GC) operation. Further details are provided in the main manuscript of the corresponding
publication linked in the Zenodo entry. For data analysis, the dilution-corrected hydrogen-in-oxygen values should be
used, as they represent the true concentrations; the uncorrected values are included solely for completeness.
Corrected gas analysis values are reported only during measurement phases in which they are meaningful—specifically,
during H2 char and CstC phases—since su fficient equilibration time is required to obtain stable and representative
signals under constant current conditions. It should also be noted that gas analysis data have a significantly lower sam-
pling rate, as measurements are conducted only every few minutes using a gas chromatograph. Consequently, these
2

PAGE 3
Table 3: Dataset column names and description
column name description
elapsed time in s overall measurement time in s
Temp in degC cell block temperature in °C, contains occasional errors and irregularities
I in mA electric current in mA
E in V total cell voltage in V
freq in Hz EIS frequency in Hz
Z magnitude in Ohm EIS magnitude of cell impedance in Ω
Z phase in deg EIS phase of cell impedance in deg
conductivity in uS/cm Water conductivity in µS/cm
pressure in bar abs Cathode cell pressure in bar absolute
H2 uncorrected in vol.% raw H 2 in O2 from GC in vol.%
H2 corrected in vol.% dilution-corrected H 2 in O2 in vol.%
measurement type contains an identifier of the current measurement type which refers to a specific step of the
measurement protocol: pressure build up, conditioning, POL GEIS, H2 char, CV cycles,
OCV , CstC12A, GEIS 12A, CstC 1A, GEIS 1A
measurement type counter counter per measurement type
columns are relatively sparse and contain a large number of NaN entries compared to continuously recorded variables
such as current or cell voltage.
Finally, protocol-related information is included to document the operational step associated with each data point.
This includes an identifier for the corresponding step in the measurement sequence and a counter for each measurement
type, facilitating, for example, the comparison of repeated measurements such as the second polarization curve across
all samples.
The general measurement protocol for all samples is illustrated as a flow chart in Figure 1. In addition, Figure 2
provides a more detailed representation of the individual measurement phases and includes exemplary voltage curves
for each phase to facilitate understanding. The measurement type identifiers introduced in Table 3 are also explained
in greater detail in Figure 2.
The core of the experimental procedure consists of recurring alternations between stress and characterization
phases. The initial characterization phase is performed twice to ensure a reliable beginning-of-test (BoT) characteri-
zation.
The experiment begins with the pressure build-up phase (Figure 2a), during which constant-current holds of ap-
proximately 15 min are applied to reach the target cathode pressure of 30 bar absolute, as no external pressure booster
is available on the test bench. Subsequently, the cells are conditioned at the target pressure for a total duration of 20.5 h
(Figure 2b).
The recurring characterization phase (Figure 2c) consists of three parts: (i) electrochemical characterization us-
ing an i/U curve combined with galvanostatic EIS measurements (measurement type identifier POL GEIS), (ii) long
constant-current (CC) holds for hydrogen crossover measurements (H2 char), and (iii) a second electrochemical char-
acterization identical to the first (POL GEIS).
The electrochemical characterization comprises 17 CC steps in the range of 0.01–3 A, cm−2, with fine increments
conditioning
pressure build up
characterization
characterization
stress phase
x5
start
end
c) 
d) 
c) 
b) 
a) 
Figure 1: Flow chart of the overall test protocol, the pressure build up phase (a), the conditioning phase (b), the characterization phase (c), and the
stress phase (d).
3

PAGE 4
a) pressure build up phase (pressure_build_up)
CstC i=[0.1, 1, 2] A cm-2
t=[0.15, 0.15, 0.15] h (approx.)
b) conditioning phase (conditioning)
CstC i=[0.1, 1, 2] A cm-2
t=[0.5, 0.5, 0.5] h
CV U=[1.9] V
t=[19] h
c) characterization phase*
*BoT characterization always performed two times for all samples
i=[0.01, ..., 3] A cm-2 in total 17 steps 
t=[30, ..., 30] s + subsequent GEIS measur.
with frequency range between 10 - 0.1 kHz
i=[0.01, ..., 3] A cm-2 in total 17 steps 
t=[30, ..., 30] s + subsequent GEIS measur.
with frequency range between 10 - 0.1 kHz
i=[0.1, 0.25, 0.5, 0.75, 1, 2, 3] A cm-2
t=[6, 5, 4, 4, 3, 2, 2] h
d) stress phase
x360
t= 300sOCV
CV U=[1.5, 1.9] V
t=[10, 10] s
x22
i=[3, 0.25] A cm-2
t=[2, 5] h + subsequent GEIS measur.CstC
[+GEIS] with frequency range between 10 - 0.1 kHz
conditioning
pressure_build_up 
POL_GEIS
H2_char
POL_GEIS
CV_cycles
OCV
CstC_12A GEIS_12A
CstC_1A
GEIS_1A 
+ ( )+ H2_charPOL_GEIS  POL_GEIS  
+ + + + 
+ 
CV_cycles OCV CstC_12A
CstC_1A
GEIS_12A
GEIS_1A
(
)
POL_GEIS  
POL_GEIS  
H2_char
Figure 2: Detailed description of the test phases, including the assignment of the individual measurement types from Table 3 (left hand side).
Example of the resulting cell voltage for each individual phase, for better understanding (right hand side).
4

PAGE 5
of 0.01 A, cm−2 in the Tafel region and larger increments above 0.1 A , cm−2. Each step is held for 30 s, followed by
a galvanostatic EIS measurement with an amplitude of 10% of the applied current. In some cases, the lowest current
densities (0.01 and 0.02 A , cm−2) do not exceed the electrolysis threshold. This behavior is most likely caused by
hydrogen crossover at elevated cathode pressure. Under these conditions, the hydrogen oxidation reaction occurs at
the anode instead of the oxygen evolution reaction. Further details are provided in the original publication linked in
the corresponding Zenodo entry.
The subsequent CC holds, with durations between 2 h and 6 h, are used to determine the hydrogen concentration
in the oxygen stream at the anode outlet for the respective applied current. The required duration depends strongly
on the experimental setup—particularly the gas volume in the anode line downstream of the cell—and on the applied
current density, as steady-state conditions must be reached for each operating point.
The stress phases, lasting approximately 235 h, consist of several steps. First, voltage cycling between 1.5 V and
1.9 V is applied with 10 s hold times for a total duration of 2 h (360 cycles; measurement type identifier CV cycles).
These cycles are intended to modify the potential distribution at platinum sites in the GRC layer and thereby induce
degradation. Subsequently, the current is interrupted for 5 min and the open-circuit voltage (OCV) decay is recorded
(measurement type identifier OCV). This step intentionally creates a hydrogen oversupply due to the pressure dif-
ferential, causing the cell voltage to drop below the electrolysis threshold ( ≈1.4 V), which further stresses the GRC
layer. Finally, two constant-current holds are applied: 2 h at 3 .0 A , cm−2 and 5 h at 0 .25 A , cm−2, each followed
by a GEIS measurement (measurement type identifiers CstC 12A, GEIS 12A, CstC 1A, and GEIS 1A). These steps
simulate prolonged high-load and part-load operation and enable monitoring of voltage, hydrogen crossover, and
high-frequency resistance (HFR) over time.
After six cycles of characterization and stress phases—corresponding to a total test duration of approximately
1,500 h—an end-of-test (EoT) characterization is performed, identical to the BoT characterization. To facilitate data
handling, several examples are provided to illustrate how filtering specific columns affects data selection (also included
in the accompanying Jupyter notebook):
• Selecting rows where the measurement type is POL GEIS and the measurement counter equals 5 → yields the
polarization curve (including associated CC and GEIS steps) for the fifth measured polarization curve
• Additionally selecting rows where the frequency column is NaN → isolates the constant-current (CstC) seg-
ments of the selected POL GEIS measurement.
• Selecting rows where the frequency column is not NaN → extracts only the EIS data, e.g., for evaluating the
high-frequency resistance (HFR).
4. Limitations and Additional Information
This section outlines specific characteristics and limitations of the dataset that should be considered during analy-
sis. Due to the use of a multi-channel potentiostat, in which only one channel can perform electrochemical impedance
spectroscopy (EIS) at a time, waiting periods frequently occur before EIS measurements. During these intervals, the
system is held at the previous operating point.
The reported temperature corresponds to the cell block temperature. Although the circulating water is heated to
80 °C, the actual reaction temperature within the cell cannot be determined more precisely. Additionally, self-heating
of the cell at high current densities can be observed in the measurement data.
As a general convention, dataset columns contain NaN values whenever no measurement is available (e.g., EIS-
related columns during constant-current (CstC) phases).
Regarding the electrical setup, the anode and cathode current cables are twisted together, and the corresponding
voltage sensing leads are arranged in the same manner. The PtNano and PtBlack samples were operated simultaneously
on two separate channels of the same test bench; the same applies to the Pt /C and Reference samples. Between
approximately 300 h and 500 h of operation, the test bench experienced a temporary connection error a ffecting both
pressure and conductivity measurements for the PtNano and PtBlack experiments. Consequently, the corresponding
data columns contain NaN values during this time interval.
5