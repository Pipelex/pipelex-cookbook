# Key: dpe_single_page

Inputs: `assets/extract_dpe/dpe_single_page.pdf`, the first page of a French energy performance diagnostic ("Diagnostic de performance énergétique (logement)", ADEME number BJCEKAHAW32) for a 36.8 m² flat in Paris built before 1948, issued by La Société des Diags. It is the sample the example has always shipped with.

## Planted facts
F1. The dwelling's address is 51 rue du Roi de Sicile, 75004 PARIS - 4EME (ground floor, right-hand door, lot 18); the owners, M ET MME RALISSE, have their own address at 51 rue du Roi 75018 PARIS - 18EME.
F2. The diagnostic was issued ("Etabli le") on 29/03/2022 and is valid until ("Valable jusqu'au") 28/03/2032.
F3. The energy scale shows 560 kWh/m²/an of primary energy and places the dwelling in class G.
F4. The separate CO₂ scale shows 18 kg CO₂/m²/an and places the dwelling in class C; the 18 is also printed beside the energy label, next to the big G.
F5. The dwelling emits 690 kg of CO₂ per year in total, the equivalent of 3 576 km by car.
F6. The yearly energy costs are estimated between 1 260 € and 1 750 € per year.

## Must
M1. `address` names 51 rue du Roi de Sicile and the postcode 75004 Paris, in any formatting, with or without the floor, door and lot details.
M2. `date_of_issue` is 2022-03-29.
M3. `date_of_expiration` is 2032-03-28.
M4. `energy_efficiency_class` is G.
M5. `per_year_per_m2_consumption` is 560.
M6. `co2_emission_class` is C.
M7. `per_year_per_m2_co2_emissions` is 18.
M8. `yearly_energy_costs_min` is 1260 and `yearly_energy_costs_max` is 1750.

## Must not
N1. `address` giving the owners' address, 51 rue du Roi 75018 Paris.
N2. `co2_emission_class` read as G, the energy class printed beside the 18.
N3. `per_year_per_m2_co2_emissions` given as 690, the dwelling's yearly total, instead of 18 per m².
N4. `date_of_expiration` given as 2032-03-29, ten years to the day after the issue, instead of the printed 28 March 2032.

## Also acceptable
A1. `address` keeping "PARIS - 4EME" or writing "Paris 4e", for M1.

## Pass bar
Every Must and Must not line.
