clear all
set more off
set mem 10000000
set matsize 10000

**************************************
*** NSS Panel Merge ******************
**************************************

** Set file paths
do "$path_code/paths.do"

********************************************************************************
********************************************************************************

** Step 1: Construct crosswalk for 2000 NSS state/district codes (from 1991 to 2001)
{

	// Merge 2000 NSS with 1991 PCA (including 1991-2001 xwalk)
use "$nss/Final/nss_hhlevel_clean_withframepops.dta", clear
keep if year=="1999-2000"
replace year = substr(year,-4,4)
destring year, replace
rename state st_code91
rename district dt_code91
destring st_code91 dt_code91, replace
collapse (sum) wgt_combined, by(st_code91 dt_code91 year)
merge 1:m st_code91 dt_code91 using "$pca/pca_census91.dta"

	// Find states where the merge might be off
correlate wgt_combined tot_p_91 if st_code91==2
correlate wgt_combined tot_p_91 if st_code91==3
correlate wgt_combined tot_p_91 if st_code91==4
correlate wgt_combined tot_p_91 if st_code91==5 // BIHAR+JHARKHAND a problem
correlate wgt_combined tot_p_91 if st_code91==7
correlate wgt_combined tot_p_91 if st_code91==8
correlate wgt_combined tot_p_91 if st_code91==9
correlate wgt_combined tot_p_91 if st_code91==11
correlate wgt_combined tot_p_91 if st_code91==12
correlate wgt_combined tot_p_91 if st_code91==13
correlate wgt_combined tot_p_91 if st_code91==14
correlate wgt_combined tot_p_91 if st_code91==15
correlate wgt_combined tot_p_91 if st_code91==16
correlate wgt_combined tot_p_91 if st_code91==17
correlate wgt_combined tot_p_91 if st_code91==18
correlate wgt_combined tot_p_91 if st_code91==19 // ORISSA a problem
correlate wgt_combined tot_p_91 if st_code91==20
correlate wgt_combined tot_p_91 if st_code91==21
correlate wgt_combined tot_p_91 if st_code91==22
correlate wgt_combined tot_p_91 if st_code91==23 // TAMIL NADU might be a problem
correlate wgt_combined tot_p_91 if st_code91==24 
correlate wgt_combined tot_p_91 if st_code91==25 // UP has many unmatched
correlate wgt_combined tot_p_91 if st_code91==26

	// Flag states with iffy matches
gen flag_91_match_iffy = inlist(st_code91,5,19,23,25)

	// Drop states with a match
egen temp = mode(st_code), by(st_code91)
replace st_code = temp if _merge==1
drop if _merge==2

	// Clean up and save
keep st_code91 dt_code91 year st_code dt_code flag_91_match_iffy
rename st_code91 st_codeNSS
rename dt_code91 dt_codeNSS
duplicates drop
duplicates t st_codeNSS dt_codeNSS, gen(dup91)
tempfile xwalk91
save `xwalk91'

	// Reload full NSS panel
use "$nss/Final/nss_hhlevel_clean_withframepops.dta", clear

	// Make year numeric
tab year
replace year = substr(year,-4,4)
destring year, replace

	// Rejigger 2010 district codes
tab district if year==2010
assert length(district)<=2 if year<2010
assert length(district)>=2 if year>=2010
replace district = substr(district,-2,2) if year>=2010 
destring state district year nss nsc, replace
tab year, missing
tab nss, missing
tab nsc, missing
assert mi(state) + mi(district) + mi(year) + mi(nss) + mi(nsc)==0
rename state st_code
rename district dt_code
duplicates t st_code dt_code, gen(dup)
drop dup

	// Collapse to district level
collapse (sum) sum_wgt_combined = wgt_combined, by(st_code dt_code year)

	// Store NSS codes, for collapsing with weights
rename st_code st_codeNSS 
rename dt_code dt_codeNSS
destring st_codeNSS dt_codeNSS, replace

joinby st_codeNSS dt_codeNSS year using `xwalk91', unmatched(both)
tab _merge year
assert _merge==3 if year==2000
assert _merge==1 if year!=2000

order st_code dt_code
sort st_code dt_code year
replace st_code = st_codeNSS if _merge==1 
replace dt_code = dt_codeNSS if _merge==1
tab year if st_code==. | dt_code==.
tab year if st_code==. & dt_code==.
drop _merge

la var st_codeNSS "NSS state code, for collapsing to district level" 
la var dt_codeNSS "NSS district code, for collapsing to district level"
la var st_code "2001 state code, for linking to 2001 census" 
la var dt_code "2001 district code, for linking to 2001 census"
la var flag_91_match_iffy "Flag for states with iffy 1991-2001 district matches"
la var dup91 "# duplicates of base 1991 district in 2001 (due to district splits)"

compress
save "$nss/nss_xwalk_2001codes.dta", replace
}

********************************************************************************
********************************************************************************

** Step 2: Process and collapse NSS into district x year panel
{

use "$nss/Final/nss_hhlevel_clean_withframepops.dta", clear

	// Make year numeric
tab year
replace year = substr(year,-4,4)
destring year, replace

	// Rejigger 2010 district codes
tab district if year==2010
assert length(district)<=2 if year<2010
assert length(district)>=2 if year>=2010
replace district = substr(district,-2,2) if year>=2010 
destring state district year nss nsc, replace
tab year, missing
tab nss, missing
tab nsc, missing
assert mi(state) + mi(district) + mi(year) + mi(nss) + mi(nsc)==0

	// Rename codes to distinguish between the ones we'll use to merge
rename state st_codeNSS
rename district dt_codeNSS
la var st_codeNSS "NSS state code, for collapsing to district level" 
la var dt_codeNSS "NSS district code, for collapsing to district level"

	// Fix units on electricity quantity
tabstat electricity_quantity if electricity_quantity>0, by(year) s(min p5 p10 p25 p50 p75 p90 p95 max)
replace electricity_quantity = electricity_quantity*1000 if year==2010
tabstat electricity_quantity if electricity_quantity>0, by(year) s(min p5 p10 p25 p50 p75 p90 p95 max)
la var electricity_quantity "Total quantity of electricity (kWh)"

	// Fix units on electricity price
tabstat implied_elec_price if electricity_quantity>=0, by(year) s(min p5 p10 p25 p50 p75 p90 p95 max)
replace implied_elec_price = implied_elec_price/1000 if year==2010
tabstat implied_elec_price if electricity_quantity>0, by(year) s(min p5 p10 p25 p50 p75 p90 p95 max)
la var implied_elec_price "Avg electricity price (Rs/kWh)"
	
	// Electricity quantity dummy
gen double elec_q_yn = 0
replace elec_q_yn = 1 if electricity_quantity>0 & electricity_quantity!=.
la var elec_q_yn "Dummy for non-zero HH-level elec consumption"

	// Inflate all rupees to 2010 levels (there was hella inflation in India between 2000 and 2010)
preserve 
import excel "$nss/INDCPIALLAINMEI.xls", sheet("FRED Graph") cellrange(A11:B33) firstrow clear
gen year = year(observation_date)
sum IND if year==2010
local cpi2010 = r(mean)
gen INDdef = IND/`cpi2010'
keep year INDdef
tempfile INDdef
save `INDdef'
restore
merge m:1 year using `INDdef', keep(1 3)
assert _merge==3
foreach v of varlist monthly_per_capita_exp_30 fuellight_value other_fuel_value electricity_value implied_elec_price {
	replace `v' = `v'/INDdef
}
drop INDdef _merge

	// Some data checks
tab elec_q_yn elec_light_yn if year==2000	
tab elec_q_yn elec_light_yn if year==2005
tab elec_q_yn elec_light_yn if year==2010
tab elec_q_yn fan_yn if year==2000	
tab elec_q_yn fan_yn if year==2005
tab elec_q_yn fan_yn if year==2010
tab elec_light_yn fan_yn if year==2000	
tab elec_light_yn fan_yn if year==2005
tab elec_light_yn fan_yn if year==2010
tab elec_light_yn tv_yn if year==2000	
tab elec_light_yn tv_yn if year==2005
tab elec_light_yn tv_yn if year==2010
tab elec_light_yn ac_yn if year==2000	
tab elec_light_yn ac_yn if year==2005
tab elec_light_yn ac_yn if year==2010
replace ac_yn = . if ac_yn==4
tab elec_q_yn ac_yn if year==2000	
tab elec_q_yn ac_yn if year==2005
tab elec_q_yn ac_yn if year==2010

tabstat monthly_per_capita_exp_30, by(year) s(min p5 p10 p25 p50 p75 p90 p95 max)
twoway ///
	(kdensity monthly_per_capita_exp_30 if year==2000 & monthly_per_capita_exp_30 < 3000) ///
	(kdensity monthly_per_capita_exp_30 if year==2005 & monthly_per_capita_exp_30 < 3000) ///
	(kdensity monthly_per_capita_exp_30 if year==2010 & monthly_per_capita_exp_30 < 3000) ///
	, legend(order(1 "2000" 2 "2005" 3 "2010"))

twoway ///
	(kdensity electricity_quantity if year==2000 & electricity_quantity<200) ///
	(kdensity electricity_quantity if year==2005 & electricity_quantity<200) ///
	(kdensity electricity_quantity if year==2010 & electricity_quantity<200) ///
	, legend(order(1 "2000" 2 "2005" 3 "2010"))

twoway ///
	(kdensity electricity_quantity if year==2000 & electricity_quantity<200 & electricity_quantity>0) ///
	(kdensity electricity_quantity if year==2005 & electricity_quantity<200 & electricity_quantity>0) ///
	(kdensity electricity_quantity if year==2010 & electricity_quantity<200 & electricity_quantity>0) ///
	, legend(order(1 "2000" 2 "2005" 3 "2010"))
	
	
	// 1999-2000 weights
/*
wgt_subsample = MLT/400 (double it if urban in state 32)
if NSS>NSC wgt_combined = MLT/800, else wgt_combined = MLT/400 (double it if urban in state 32)
*/
assert mult!=. if year==2000
gen temp1 = mult/400
tab nss nsc if year==2000
br st_code dt_code year nss nsc mult wgt* temp1 if year==2000
correlate temp1 wgt_subsample if year==2000
reg wgt_subsample temp1 if year==2000
gen temp2 = mult/800
replace temp2 = mult/400 if nss==nsc
gen temp3 = abs(temp1-wgt_subsample)
gen temp4 = abs(temp2-wgt_combined)
sum temp3 temp4 if year==2000, detail
assert temp3<0.1 & temp4<0.1 if year==2000
drop temp*
/* the codebook should read "NSS>NSC", which makes everything check out perfectly*/

	// 2004-2005 weights
/*
subsample estimates: weight = MLT/100
subsample-combined estimates: if NSS=NSC weight = MLT/100, else weight = MLT/200
*/
assert mlt!=. if year==2005
gen temp1 = mlt/100
gen temp2 = mlt/100
replace temp2 = mlt/200 if nss!=nsc
gen temp3 = abs(temp1-wgt_subsample)
gen temp4 = abs(temp2-wgt_combined)
sum temp3 temp4 if year==2005, detail
assert temp3<0.1 & temp4<0.1 if year==2005
drop temp*


	// 2009-2010 weights
assert mlt!=. if year==2010
gen temp1 = mlt/100
replace temp1 = mlt/200 if nss!=nsc
gen temp3 = abs(temp1-multiplier)
sum temp3 if year==2010, detail
assert temp3<0.1 if year==2010
drop temp*

	// Assign weights = combined weights
gen WT = wgt_combined
replace WT = multiplier if year==2010	

	// Assess population growth: survey year - 2001 Census
correlate frame_population approx_present_pop
gen temp = approx_present_pop - frame_population
sum temp if year==2005, detail
sum temp if year==2010, detail
drop temp
	// this is basically exponential growth!
	
	// Merge in 2001 district populations (summed over all rural villages, for 2005-10 waves)
preserve
use "$panel/panel_dataset_no_outcomes.dta", clear
collapse (sum) tot_p_dist01=tot_p, by(st_code dt_code state)
hist tot_p_dist01
merge 1:m st_code dt_code using "$nss/nss_xwalk_2001codes.dta"
drop if year==2000
unique st_codeNSS dt_codeNSS year if _merge!=1
assert r(unique)==r(N)
drop if _merge==1
keep tot_p_dist01 st_codeNSS dt_codeNSS year
tempfile district_pops01
save `district_pops01'
restore
merge m:1 st_codeNSS dt_codeNSS year using `district_pops01'
assert _merge==3 if year!=2000
assert _merge==1 if year==2000
drop _merge

	// Merge in 1991 district populations (summed over all rural villages, for 2000 wave)
preserve
use "$pca/pca_census91_st_dist.dta", clear
keep t_popln_r91 st_code91 dist_code91
rename st_code91 st_codeNSS
rename dist_code91 dt_codeNSS
destring st_codeNSS dt_codeNSS, replace
merge 1:m st_codeNSS dt_codeNSS using "$nss/nss_xwalk_2001codes.dta"
drop if year!=2000
drop st_code dt_code 
duplicates drop
tab _merge
unique st_codeNSS dt_codeNSS year
assert r(unique)==r(N)
drop if _merge==1
rename t_popln_r91 tot_p_dist91
keep tot_p_dist91 st_codeNSS dt_codeNSS year
tempfile district_pops91
save `district_pops91'
restore
merge m:1 st_codeNSS dt_codeNSS year using `district_pops91'
assert _merge==3 if year==2000
assert _merge==1 if year!=2000
drop _merge

	// District population deciles
gen tot_p_dist = tot_p_dist01
replace tot_p_dist = tot_p_dist91 if year==2000 & tot_p_dist==.
tab st_codeNSS year if tot_p_dist==.
egen temp_tag = tag(st_codeNSS dt_codeNSS year)	
gen dist_pop_decile = .
forvalues p = 1(1)9 {
	egen temp1 = pctile(tot_p_dist) if temp_tag, p(`p'0) by(year)
	egen temp2 = mean(temp1), by(year)
	replace dist_pop_decile = `p' if tot_p_dist<=temp2 & dist_pop_decile==.
	drop temp1 temp2
}
replace dist_pop_decile = 10 if dist_pop_decile==. & tot_p_dist!=.
drop tot_p_dist01 tot_p_dist91 temp_tag


	// Populations by weight decile
preserve
collapse(max) WT (count) count=WT (sum) sum_WT=WT, by(frame_population approx_present_pop ///
	st_codeNSS dt_codeNSS fsu_serial year dist_pop_decile)
unique fsu_serial_no
assert r(unique)==r(N)

gen WT_decile = .
forvalues p = 1(1)9 {
	egen temp = pctile(WT), p(`p'0) by(year)
	replace WT_decile = `p' if WT<=temp & WT_decile==.
	drop temp
}
replace WT_decile = 10 if WT_decile==. & WT!=.

gen pop_decile = .
forvalues p = 1(1)9 {
	egen temp = pctile(frame_population), p(`p'0) by(year)
	replace pop_decile = `p' if frame_population<=temp & pop_decile==.
	drop temp
}
replace pop_decile = 10 if pop_decile==. & frame_pop!=.

gen ppop_decile = .
forvalues p = 1(1)9 {
	egen temp = pctile(approx_present_pop), p(`p'0) by(year)
	replace ppop_decile = `p' if approx_present_pop<=temp & ppop_decile==.
	drop temp
}
replace ppop_decile = 10 if ppop_decile==. & approx_present_pop!=.

tab WT_decile pop_decile if year==2005 
tab dist_pop_decile pop_decile if year==2005

tab pop_decile if year==2005 & WT_decile<=3
tab pop_decile if year==2005 & dist_pop_decile<=3
tab pop_decile if year==2005 & (WT_decile<=3 | dist_pop_decile<=3)
unique st_codeNSS dt_codeNSS if year==2005 & WT_decile<=3
unique st_codeNSS dt_codeNSS if year==2005 & dist_pop_decile<=3
unique st_codeNSS dt_codeNSS if year==2005 & (WT_decile<=3 | dist_pop_decile<=3)

tab pop_decile if year==2005 & WT_decile<=5
tab pop_decile if year==2005 & dist_pop_decile<=5
tab pop_decile if year==2005 & (WT_decile<=5 | dist_pop_decile<=5)
unique st_codeNSS dt_codeNSS if year==2005 & WT_decile<=5
unique st_codeNSS dt_codeNSS if year==2005 & dist_pop_decile<=5
unique st_codeNSS dt_codeNSS if year==2005 & (WT_decile<=5 | dist_pop_decile<=5)

tab WT_decile dist_pop_decile if year==2005
tab WT_decile dist_pop_decile if year==2010
tab WT_decile dist_pop_decile if year==2000

keep st_codeNSS dt_codeNSS year fsu_serial_no WT WT_decile pop_decile dist_pop_decile
rename WT WT_max
compress
tempfile deciles
save `deciles'
restore

merge m:1 st_codeNSS dt_codeNSS year fsu_serial_no using `deciles'
assert _merge==3
drop _merge


	// Populations by weight quartile
preserve
collapse (max) WT (count) count=WT (sum) sum_WT=WT, by(frame_population approx_present_pop ///
	st_codeNSS dt_codeNSS fsu_serial year)
unique fsu_serial_no
assert r(unique)==r(N)

gen WT_quartile = .
forvalues p = 1(1)3 {
	local q = `p'*25
	egen temp = pctile(WT), p(`q') by(year)
	replace WT_quartile = `p' if WT<=temp & WT_quartile==.
	drop temp
}
replace WT_quartile = 4 if WT_quartile==. & WT!=.

gen pop_quartile = .
forvalues p = 1(1)3 {
	local q = `p'*25
	egen temp = pctile(frame_population), p(`q') by(year)
	replace pop_quartile = `p' if frame_population<=temp & pop_quartile==.
	drop temp
}
replace pop_quartile = 4 if pop_quartile==. & frame_pop!=.

tab WT_quartile pop_quartile if year==2005 
tab WT_quartile pop_quartile if year==2010 

tabstat frame_population if year==2005, by(WT_quartile) s(p10 p25 p50 p75 p90 n)
tabstat frame_population if year==2010, by(WT_quartile) s(p10 p25 p50 p75 p90 n)

keep st_codeNSS dt_codeNSS year fsu_serial_no WT_quartile pop_quartile 
compress
tempfile quartiles
save `quartiles'
restore

merge m:1 st_codeNSS dt_codeNSS year fsu_serial_no using `quartiles'
assert _merge==3
drop _merge

	
	// Save uncollapsed dataset that renormalizes weights within each district-year to 1
preserve
egen temp_denom = sum(WT), by(st_codeNSS dt_codeNSS year)
gen weight_normalized = WT/temp_denom*1e6
drop nss nsc mult mlt multiplier wgt* WT WT_max temp_denom
la var weight_normalized "NSS weight, normalized to sum to 1 within district-year"
la var fsu_serial_no "NSS unique village identifier"
la var WT_decile "Decile of max(NSS weights) by village, within year"
la var pop_decile "Decile of village population, within year"
la var dist_pop_decile "Decile of district rural population, within year"
la var tot_p_dist "Total rural population of district, within year"
la var WT_quartile "Quartile of max(NSS weights) by village, within year"
la var pop_quartile "Quartile of village population, within year"
compress
save "$nss/nss_hhlevel_uncollapsed_nss_codes.dta", replace
restore		
	
	
	// Assess 2001 population distribution, weighted
assert frame_population==. if year==2000
sum frame_population if year==2005 [fw=round(WT*100)], detail
sum frame_population if year==2010 [fw=round(WT*100)], detail

sum frame_population if year==2005 [fw=round(WT*100)], detail
local n2005 = r(N)
sum frame_population if year==2010 [fw=round(WT*100)], detail
local n2010 = r(N)

sum frame_population if year==2005 & frame_population<=500 [fw=round(WT*100)], detail // 8% of villages, mean = 319, median = 329
di r(N)/`n2005'
sum frame_population if year==2010 & frame_population<=500 [fw=round(WT*100)], detail // 8% of villages, mean = 325, median = 339
di r(N)/`n2010'

sum frame_population if year==2005 & frame_population>500 & frame_population<=1000 [fw=round(WT*100)], detail // 14% of villages, mean = 757, median = 769
di r(N)/`n2005'
sum frame_population if year==2010 & frame_population>500 & frame_population<=1000 [fw=round(WT*100)], detail // 14% of villages, mean = 749, median = 749
di r(N)/`n2010'

sum frame_population if year==2005 & frame_population<=1000 [fw=round(WT*100)], detail // 22% of villages, mean = 601, median = 621
di r(N)/`n2005'
sum frame_population if year==2010 & frame_population<=1000 [fw=round(WT*100)], detail // 22% of villages, mean = 595, median = 618
di r(N)/`n2010'

sum frame_population if year==2005 & frame_population>1000 & frame_population<=2000 [fw=round(WT*100)], detail // 25% of villages, mean = 1488, median = 1488
di r(N)/`n2005'
sum frame_population if year==2010 & frame_population>1000 & frame_population<=2000 [fw=round(WT*100)], detail // 26% of villages, mean = 1475, median = 1480
di r(N)/`n2010'

sum frame_population if year==2005 & frame_population>2000 & frame_population<=4000 [fw=round(WT*100)], detail // 27% of villages, mean = 2816, median = 2711
di r(N)/`n2005'
sum frame_population if year==2010 & frame_population>2000 & frame_population<=4000 [fw=round(WT*100)], detail // 26% of villages, mean = 2808, median = 2705
di r(N)/`n2010'

sum frame_population if year==2005 & frame_population>4000 [fw=round(WT*100)], detail // 26% of villages, mean = 8490, median = 6532
di r(N)/`n2005'
sum frame_population if year==2010 & frame_population>4000 [fw=round(WT*100)], detail // 26% of villages, mean = 8669, median = 6578
di r(N)/`n2010'
	// will use cutoffs of 500, 1000, 2000, and 4000


	// National income quartiles by year (weighted)
gen exp_n_yr_p25 = .
gen exp_n_yr_p50 = .
gen exp_n_yr_p75 = .

sum monthly_per_capita_exp_30 if year==2000 [fw=round(WT*100)], detail // median 446 Rs/month
replace exp_n_yr_p25 = r(p25) if year==2000
replace exp_n_yr_p50 = r(p50) if year==2000
replace exp_n_yr_p75 = r(p75) if year==2000

sum monthly_per_capita_exp_30 if year==2005 [fw=round(WT*100)], detail // median 483 Rs/month
replace exp_n_yr_p25 = r(p25) if year==2005
replace exp_n_yr_p50 = r(p50) if year==2005
replace exp_n_yr_p75 = r(p75) if year==2005

sum monthly_per_capita_exp_30 if year==2010 [fw=round(WT*100)], detail // median 814 Rs/month
replace exp_n_yr_p25 = r(p25) if year==2010
replace exp_n_yr_p50 = r(p50) if year==2010
replace exp_n_yr_p75 = r(p75) if year==2010


	// District-year income quartiles (weighted)
gen exp_d_yr_p25 = .
gen exp_d_yr_p50 = .
gen exp_d_yr_p75 = .
egen stdt = group(st_codeNSS dt_codeNSS)
levelsof stdt, local(levs)
foreach i in `levs' {
	foreach y in 2000 2005 2010 {
		qui sum monthly_per_capita_exp_30 if stdt==`i' & year==`y', detail
		replace exp_d_yr_p25 = r(p25) if stdt==`i' & year==`y'
		replace exp_d_yr_p50 = r(p50) if stdt==`i' & year==`y'
		replace exp_d_yr_p75 = r(p75) if stdt==`i' & year==`y'
	}
}
assert exp_d_yr_p25!=. & exp_d_yr_p50!=. & exp_d_yr_p75!=.
hist exp_d_yr_p50 if year==2005

	
	// Weighted collapse
	
	// Denominators for full collapse
egen double sum_wgts = sum(WT), by(st_codeNSS dt_codeNSS year)
assert WT!=.
la var sum_wgts "Sum of NSS weights by stdt-year"

	// Denominators for 2001 population above/below 500
egen double temp_sum_wgts_under500 = sum(WT) if frame_population<=500 & frame_population!=. , by(st_codeNSS dt_codeNSS year)	
egen double temp_sum_wgts_over500 = sum(WT) if frame_population>500 & frame_population!=. , by(st_codeNSS dt_codeNSS year)
egen double sum_wgts_under500 = mean(temp_sum_wgts_under500), by(st_codeNSS dt_codeNSS year)	
egen double sum_wgts_over500 = mean(temp_sum_wgts_over500), by(st_codeNSS dt_codeNSS year)	
drop temp*
la var sum_wgts_under500 "Sum of NSS weights by stdt-year (2001 pop <=500)"
la var sum_wgts_over500 "Sum of NSS weights by stdt-year (2001 pop >500)"

	// Denominators for 2001 population above/below 1000
egen double temp_sum_wgts_under1k = sum(WT) if frame_population<=1000 & frame_population!=. , by(st_codeNSS dt_codeNSS year)	
egen double temp_sum_wgts_over1k = sum(WT) if frame_population>1000 & frame_population!=. , by(st_codeNSS dt_codeNSS year)
egen double sum_wgts_under1k = mean(temp_sum_wgts_under1k), by(st_codeNSS dt_codeNSS year)	
egen double sum_wgts_over1k = mean(temp_sum_wgts_over1k), by(st_codeNSS dt_codeNSS year)	
drop temp*
la var sum_wgts_under1k "Sum of NSS weights by stdt-year (2001 pop <=1000)"
la var sum_wgts_over1k "Sum of NSS weights by stdt-year (2001 pop >1000)"

	// Denominators for 2001 population above/below 2000
egen double temp_sum_wgts_under2k = sum(WT) if frame_population<=2000 & frame_population!=. , by(st_codeNSS dt_codeNSS year)	
egen double temp_sum_wgts_over2k = sum(WT) if frame_population>2000 & frame_population!=. , by(st_codeNSS dt_codeNSS year)
egen double sum_wgts_under2k = mean(temp_sum_wgts_under2k), by(st_codeNSS dt_codeNSS year)	
egen double sum_wgts_over2k = mean(temp_sum_wgts_over2k), by(st_codeNSS dt_codeNSS year)	
drop temp*
la var sum_wgts_under2k "Sum of NSS weights by stdt-year (2001 pop <=2000)"
la var sum_wgts_over2k "Sum of NSS weights by stdt-year (2001 pop >2000)"

	// Denominators for 2001 population above/below 4000
egen double temp_sum_wgts_under4k = sum(WT) if frame_population<=4000 & frame_population!=. , by(st_codeNSS dt_codeNSS year)	
egen double temp_sum_wgts_over4k = sum(WT) if frame_population>4000 & frame_population!=. , by(st_codeNSS dt_codeNSS year)
egen double sum_wgts_under4k = mean(temp_sum_wgts_under4k), by(st_codeNSS dt_codeNSS year)	
egen double sum_wgts_over4k = mean(temp_sum_wgts_over4k), by(st_codeNSS dt_codeNSS year)	
drop temp*
la var sum_wgts_under4k "Sum of NSS weights by stdt-year (2001 pop <=4000)"
la var sum_wgts_over4k "Sum of NSS weights by stdt-year (2001 pop >4000)"

	// Denominators for 2001 population in interquartile bins
egen double temp_sum_wgts_1kto2k = sum(WT) if frame_population>1000 & frame_population<=2000 & frame_population!=. , by(st_codeNSS dt_codeNSS year)	
egen double temp_sum_wgts_2kto4k = sum(WT) if frame_population>2000 & frame_population<=4000 & frame_population!=. , by(st_codeNSS dt_codeNSS year)
egen double sum_wgts_1kto2k = mean(temp_sum_wgts_1kto2k), by(st_codeNSS dt_codeNSS year)	
egen double sum_wgts_2kto4k = mean(temp_sum_wgts_2kto4k), by(st_codeNSS dt_codeNSS year)	
drop temp*
la var sum_wgts_1kto2k "Sum of NSS weights by stdt-year (2001 pop (1000,2000])"
la var sum_wgts_2kto4k "Sum of NSS weights by stdt-year (2001 pop (2000,4000])"

	// Denominators for expenditure above/below median (natl-year)
egen double temp_sum_wgts_exp_q12_n = sum(WT) if monthly_per_capita_exp_30<=exp_n_yr_p50 , by(st_codeNSS dt_codeNSS year)	
egen double temp_sum_wgts_exp_q34_n = sum(WT) if monthly_per_capita_exp_30>exp_n_yr_p50 , by(st_codeNSS dt_codeNSS year)
egen double sum_wgts_exp_q12_n = mean(temp_sum_wgts_exp_q12_n), by(st_codeNSS dt_codeNSS year)	
egen double sum_wgts_exp_q34_n = mean(temp_sum_wgts_exp_q34_n), by(st_codeNSS dt_codeNSS year)	
drop temp*
la var sum_wgts_exp_q12_n "Sum of NSS weights by stdt-year (exp <=natl-yr median)"
la var sum_wgts_exp_q34_n "Sum of NSS weights by stdt-year (exp >natl-yr median)"

	// Denominators for expenditure above/below median (dist-year)
egen double temp_sum_wgts_exp_q12_d = sum(WT) if monthly_per_capita_exp_30<=exp_d_yr_p50 , by(st_codeNSS dt_codeNSS year)	
egen double temp_sum_wgts_exp_q34_d = sum(WT) if monthly_per_capita_exp_30>exp_d_yr_p50 , by(st_codeNSS dt_codeNSS year)
egen double sum_wgts_exp_q12_d = mean(temp_sum_wgts_exp_q12_d), by(st_codeNSS dt_codeNSS year)	
egen double sum_wgts_exp_q34_d = mean(temp_sum_wgts_exp_q34_d), by(st_codeNSS dt_codeNSS year)	
drop temp*
la var sum_wgts_exp_q12_d "Sum of NSS weights by stdt-year (exp <=dist-yr median)"
la var sum_wgts_exp_q34_d "Sum of NSS weights by stdt-year (exp >dist-yr median)"

	// Denominators for expenditure by quartile (natl-year)
egen double temp_sum_wgts_exp_q1_n = sum(WT) if monthly_per_capita_exp_30<=exp_n_yr_p25 , by(st_codeNSS dt_codeNSS year)	
egen double temp_sum_wgts_exp_q2_n = sum(WT) if monthly_per_capita_exp_30>exp_n_yr_p25 & monthly_per_capita_exp_30<=exp_n_yr_p50 , by(st_codeNSS dt_codeNSS year)	
egen double temp_sum_wgts_exp_q3_n = sum(WT) if monthly_per_capita_exp_30>exp_n_yr_p50 & monthly_per_capita_exp_30<=exp_n_yr_p75 , by(st_codeNSS dt_codeNSS year)	
egen double temp_sum_wgts_exp_q4_n = sum(WT) if monthly_per_capita_exp_30>exp_n_yr_p75 , by(st_codeNSS dt_codeNSS year)	
egen double sum_wgts_exp_q1_n = mean(temp_sum_wgts_exp_q1_n), by(st_codeNSS dt_codeNSS year)	
egen double sum_wgts_exp_q2_n = mean(temp_sum_wgts_exp_q2_n), by(st_codeNSS dt_codeNSS year)	
egen double sum_wgts_exp_q3_n = mean(temp_sum_wgts_exp_q3_n), by(st_codeNSS dt_codeNSS year)	
egen double sum_wgts_exp_q4_n = mean(temp_sum_wgts_exp_q4_n), by(st_codeNSS dt_codeNSS year)		
drop temp*
la var sum_wgts_exp_q1_n "Sum of NSS weights by stdt-year (exp in natl-yr 1st qrtle)"
la var sum_wgts_exp_q2_n "Sum of NSS weights by stdt-year (exp in natl-yr 2nd qrtle)"
la var sum_wgts_exp_q3_n "Sum of NSS weights by stdt-year (exp in natl-yr 3rd qrtle)"
la var sum_wgts_exp_q4_n "Sum of NSS weights by stdt-year (exp in natl-yr 4th qrtle)"

	// Denominators for expenditure by quartile (dist-year)
egen double temp_sum_wgts_exp_q1_d = sum(WT) if monthly_per_capita_exp_30<=exp_d_yr_p25 , by(st_codeNSS dt_codeNSS year)	
egen double temp_sum_wgts_exp_q2_d = sum(WT) if monthly_per_capita_exp_30>exp_d_yr_p25 & monthly_per_capita_exp_30<=exp_d_yr_p50 , by(st_codeNSS dt_codeNSS year)	
egen double temp_sum_wgts_exp_q3_d = sum(WT) if monthly_per_capita_exp_30>exp_d_yr_p50 & monthly_per_capita_exp_30<=exp_d_yr_p75 , by(st_codeNSS dt_codeNSS year)	
egen double temp_sum_wgts_exp_q4_d = sum(WT) if monthly_per_capita_exp_30>exp_d_yr_p75 , by(st_codeNSS dt_codeNSS year)	
egen double sum_wgts_exp_q1_d = mean(temp_sum_wgts_exp_q1_d), by(st_codeNSS dt_codeNSS year)	
egen double sum_wgts_exp_q2_d = mean(temp_sum_wgts_exp_q2_d), by(st_codeNSS dt_codeNSS year)	
egen double sum_wgts_exp_q3_d = mean(temp_sum_wgts_exp_q3_d), by(st_codeNSS dt_codeNSS year)	
egen double sum_wgts_exp_q4_d = mean(temp_sum_wgts_exp_q4_d), by(st_codeNSS dt_codeNSS year)		
drop temp*
la var sum_wgts_exp_q1_d "Sum of NSS weights by stdt-year (exp in dist-yr 1st qrtle)"
la var sum_wgts_exp_q2_d "Sum of NSS weights by stdt-year (exp in dist-yr 2nd qrtle)"
la var sum_wgts_exp_q3_d "Sum of NSS weights by stdt-year (exp in dist-yr 3rd qrtle)"
la var sum_wgts_exp_q4_d "Sum of NSS weights by stdt-year (exp in dist-yr 4th qrtle)"

	// Denominators for above/below expendiure median (natl-year) AND above/below 2000 people
egen double temp_sum_wgts_under2k_q12_n = sum(WT) if frame_population<=2000 & frame_population!=. & monthly_per_capita_exp_30<=exp_n_yr_p50 , by(st_codeNSS dt_codeNSS year)	
egen double temp_sum_wgts_under2k_q34_n = sum(WT) if frame_population<=2000 & frame_population!=. & monthly_per_capita_exp_30>exp_n_yr_p50 , by(st_codeNSS dt_codeNSS year)	
egen double temp_sum_wgts_over2k_q12_n = sum(WT) if frame_population>2000 & frame_population!=. & monthly_per_capita_exp_30<=exp_n_yr_p50 , by(st_codeNSS dt_codeNSS year)	
egen double temp_sum_wgts_over2k_q34_n = sum(WT) if frame_population>2000 & frame_population!=. & monthly_per_capita_exp_30>exp_n_yr_p50 , by(st_codeNSS dt_codeNSS year)	
egen double sum_wgts_under2k_exp_q12_n = mean(temp_sum_wgts_under2k_q12_n), by(st_codeNSS dt_codeNSS year)	
egen double sum_wgts_under2k_exp_q34_n = mean(temp_sum_wgts_under2k_q34_n), by(st_codeNSS dt_codeNSS year)	
egen double sum_wgts_over2k_exp_q12_n = mean(temp_sum_wgts_over2k_q12_n), by(st_codeNSS dt_codeNSS year)	
egen double sum_wgts_over2k_exp_q34_n = mean(temp_sum_wgts_over2k_q34_n), by(st_codeNSS dt_codeNSS year)	
drop temp*
la var sum_wgts_under2k_exp_q12_n "Sum of NSS weights by stdt-year (2001 pop <=2000, exp <=natl-yr median)"
la var sum_wgts_under2k_exp_q34_n "Sum of NSS weights by stdt-year (2001 pop >2000, exp >natl-yr median)"
la var sum_wgts_over2k_exp_q12_n "Sum of NSS weights by stdt-year (2001 pop <=2000, exp <=natl-yr median)"
la var sum_wgts_over2k_exp_q34_n "Sum of NSS weights by stdt-year (2001 pop >2000, exp >natl-yr median)"

	// Denominators for above/below expendiure median (dist-year) AND above/below 2000 people
egen double temp_sum_wgts_under2k_q12_d = sum(WT) if frame_population<=2000 & frame_population!=. & monthly_per_capita_exp_30<=exp_d_yr_p50 , by(st_codeNSS dt_codeNSS year)	
egen double temp_sum_wgts_under2k_q34_d = sum(WT) if frame_population<=2000 & frame_population!=. & monthly_per_capita_exp_30>exp_d_yr_p50 , by(st_codeNSS dt_codeNSS year)	
egen double temp_sum_wgts_over2k_q12_d = sum(WT) if frame_population>2000 & frame_population!=. & monthly_per_capita_exp_30<=exp_d_yr_p50 , by(st_codeNSS dt_codeNSS year)	
egen double temp_sum_wgts_over2k_q34_d = sum(WT) if frame_population>2000 & frame_population!=. & monthly_per_capita_exp_30>exp_d_yr_p50 , by(st_codeNSS dt_codeNSS year)	
egen double sum_wgts_under2k_exp_q12_d = mean(temp_sum_wgts_under2k_q12_d), by(st_codeNSS dt_codeNSS year)	
egen double sum_wgts_under2k_exp_q34_d = mean(temp_sum_wgts_under2k_q34_d), by(st_codeNSS dt_codeNSS year)	
egen double sum_wgts_over2k_exp_q12_d = mean(temp_sum_wgts_over2k_q12_d), by(st_codeNSS dt_codeNSS year)	
egen double sum_wgts_over2k_exp_q34_d = mean(temp_sum_wgts_over2k_q34_d), by(st_codeNSS dt_codeNSS year)	
drop temp*
la var sum_wgts_under2k_exp_q12_d "Sum of NSS weights by stdt-year (2001 pop <=2000, exp <=dist-yr median)"
la var sum_wgts_under2k_exp_q34_d "Sum of NSS weights by stdt-year (2001 pop >2000, exp >dist-yr median)"
la var sum_wgts_over2k_exp_q12_d "Sum of NSS weights by stdt-year (2001 pop <=2000, exp <=dist-yr median)"
la var sum_wgts_over2k_exp_q34_d "Sum of NSS weights by stdt-year (2001 pop >2000, exp >dist-yr median)"

	// Denominators by max(WT) quintile
egen double temp_sum_wgts_dec12 = sum(WT) if inrange(WT_decile,1,2) , by(st_codeNSS dt_codeNSS year)	
egen double temp_sum_wgts_dec34 = sum(WT) if inrange(WT_decile,3,4) , by(st_codeNSS dt_codeNSS year)	
egen double temp_sum_wgts_dec56 = sum(WT) if inrange(WT_decile,5,6) , by(st_codeNSS dt_codeNSS year)	
egen double temp_sum_wgts_dec78 = sum(WT) if inrange(WT_decile,7,8) , by(st_codeNSS dt_codeNSS year)	
egen double temp_sum_wgts_dec90 = sum(WT) if inrange(WT_decile,9,10) , by(st_codeNSS dt_codeNSS year)	
egen double sum_wgts_dec12 = mean(temp_sum_wgts_dec12), by(st_codeNSS dt_codeNSS year)	
egen double sum_wgts_dec34 = mean(temp_sum_wgts_dec34), by(st_codeNSS dt_codeNSS year)	
egen double sum_wgts_dec56 = mean(temp_sum_wgts_dec56), by(st_codeNSS dt_codeNSS year)	
egen double sum_wgts_dec78 = mean(temp_sum_wgts_dec78), by(st_codeNSS dt_codeNSS year)	
egen double sum_wgts_dec90 = mean(temp_sum_wgts_dec90), by(st_codeNSS dt_codeNSS year)	
drop temp*
la var sum_wgts_dec12 "Sum of NSS weights by stdt-year (WT deciles 1-2)"
la var sum_wgts_dec34 "Sum of NSS weights by stdt-year (WT deciles 3-4)"
la var sum_wgts_dec56 "Sum of NSS weights by stdt-year (WT deciles 5-6)"
la var sum_wgts_dec78 "Sum of NSS weights by stdt-year (WT deciles 7-8)"
la var sum_wgts_dec90 "Sum of NSS weights by stdt-year (WT deciles 9-10)"

	// Denominators by max(WT) quartile
forvalues i = 1(1)4 {
	egen double temp_sum_wgts_quart`i' = sum(WT) if WT_quartile==`i' , by(st_codeNSS dt_codeNSS year)	
	egen double sum_wgts_quart`i' = mean(temp_sum_wgts_quart`i'), by(st_codeNSS dt_codeNSS year)	
	la var sum_wgts_quart`i' "Sum of NSS weights by stdt-year (WT quartile `i')"
}
drop temp*

	// Denominators removing top max(WT) deciles one by one
forvalues i = 9(-1)3 {
	egen double temp_sum_wgts_dec1`i' = sum(WT) if inrange(WT_decile,1,`i') , by(st_codeNSS dt_codeNSS year)
	egen double sum_wgts_dec1`i' = mean(temp_sum_wgts_dec1`i'), by(st_codeNSS dt_codeNSS year)	
	la var sum_wgts_dec1`i' "Sum of NSS weights by stdt-year (WT deciles 1-`i')"
}
drop temp*

	// Opposite of the above, keeping top deciles of max(WT), one by one
forvalues i = 8(-1)2 {
	egen double temp_sum_wgts_dec`i'0 = sum(WT) if inrange(WT_decile,`i',10) , by(st_codeNSS dt_codeNSS year)
	egen double sum_wgts_dec`i'0 = mean(temp_sum_wgts_dec`i'0), by(st_codeNSS dt_codeNSS year)	
	la var sum_wgts_dec`i'0 "Sum of NSS weights by stdt-year (WT deciles `i'-10)"
}
drop temp*

	// Denominators removing top [max(WT) deciles U dist_pop deciles] one by one
forvalues i = 9(-1)2 {
	egen double temp_sum_wgts_DEC1`i' = sum(WT) if inrange(WT_decile,1,`i') | inrange(dist_pop_decile,1,`i') , by(st_codeNSS dt_codeNSS year)
	egen double sum_wgts_DEC1`i' = mean(temp_sum_wgts_DEC1`i'), by(st_codeNSS dt_codeNSS year)	
	la var sum_wgts_DEC1`i' "Sum of NSS weights by stdt-year (WT deciles 1-`i' or Dist Pop deciles 1-`i')"
}
drop temp*


	// Count number of households surveyed by category
	
	// Full NSS
egen double n_hh_surveyed = count(nss), by(st_codeNSS dt_codeNSS year)
la var n_hh_surveyed "# NSS households surveyed by stdt-year"

	// Counts for 2001 population above/below 500
egen double temp_n_hh_under500 = count(nss) if frame_population<=500 & frame_population!=. , by(st_codeNSS dt_codeNSS year)	
egen double temp_n_hh_over500 = count(nss) if frame_population>500 & frame_population!=. , by(st_codeNSS dt_codeNSS year)
egen double n_hh_under500 = mean(temp_n_hh_under500), by(st_codeNSS dt_codeNSS year)	
egen double n_hh_over500 = mean(temp_n_hh_over500), by(st_codeNSS dt_codeNSS year)	
drop temp*
la var n_hh_under500 "# NSS households surveyed by stdt-year (2001 pop <=500)"
la var n_hh_over500 "# NSS households surveyed by stdt-year (2001 pop >500)"

	// Counts for 2001 population above/below 1000
egen double temp_n_hh_under1k = count(nss) if frame_population<=1000 & frame_population!=. , by(st_codeNSS dt_codeNSS year)	
egen double temp_n_hh_over1k = count(nss) if frame_population>1000 & frame_population!=. , by(st_codeNSS dt_codeNSS year)
egen double n_hh_under1k = mean(temp_n_hh_under1k), by(st_codeNSS dt_codeNSS year)	
egen double n_hh_over1k = mean(temp_n_hh_over1k), by(st_codeNSS dt_codeNSS year)	
drop temp*
la var n_hh_under1k "# NSS households surveyed by stdt-year (2001 pop <=1000)"
la var n_hh_over1k "# NSS households surveyed by stdt-year (2001 pop >1000)"

	// Counts for 2001 population above/below 2000
egen double temp_n_hh_under2k = count(nss) if frame_population<=2000 & frame_population!=. , by(st_codeNSS dt_codeNSS year)	
egen double temp_n_hh_over2k = count(nss) if frame_population>2000 & frame_population!=. , by(st_codeNSS dt_codeNSS year)
egen double n_hh_under2k = mean(temp_n_hh_under2k), by(st_codeNSS dt_codeNSS year)	
egen double n_hh_over2k = mean(temp_n_hh_over2k), by(st_codeNSS dt_codeNSS year)	
drop temp*
la var n_hh_under2k "# NSS households surveyed by stdt-year (2001 pop <=2000)"
la var n_hh_over2k "# NSS households surveyed by stdt-year (2001 pop >2000)"

	// Counts for 2001 population above/below 4000
egen double temp_n_hh_under4k = count(nss) if frame_population<=4000 & frame_population!=. , by(st_codeNSS dt_codeNSS year)	
egen double temp_n_hh_over4k = count(nss) if frame_population>4000 & frame_population!=. , by(st_codeNSS dt_codeNSS year)
egen double n_hh_under4k = mean(temp_n_hh_under4k), by(st_codeNSS dt_codeNSS year)	
egen double n_hh_over4k = mean(temp_n_hh_over4k), by(st_codeNSS dt_codeNSS year)	
drop temp*
la var n_hh_under4k "# NSS households surveyed by stdt-year (2001 pop <=4000)"
la var n_hh_over4k "# NSS households surveyed by stdt-year (2001 pop >4000)"

	// Counts for 2001 population in quartiles 2 and 3
egen double temp_n_hh_1kto2k = count(nss) if frame_population>1000 & frame_population<=2000 & frame_population!=. , by(st_codeNSS dt_codeNSS year)	
egen double temp_n_hh_2kto4k = count(nss) if frame_population>2000 & frame_population<=4000 & frame_population!=. , by(st_codeNSS dt_codeNSS year)
egen double n_hh_1kto2k = mean(temp_n_hh_1kto2k), by(st_codeNSS dt_codeNSS year)	
egen double n_hh_2kto4k = mean(temp_n_hh_2kto4k), by(st_codeNSS dt_codeNSS year)	
drop temp*
la var n_hh_1kto2k "# NSS households surveyed by stdt-year (2001 pop (1000,2000])"
la var n_hh_2kto4k "# NSS households surveyed by stdt-year (2001 pop (2000,4000])"

	// Counts for expenditures above/below median (natl-year)
egen double temp_n_hh_exp_q12_n = count(nss) if monthly_per_capita_exp_30<=exp_n_yr_p50 , by(st_codeNSS dt_codeNSS year)	
egen double temp_n_hh_exp_q34_n = count(nss) if monthly_per_capita_exp_30>exp_n_yr_p50 , by(st_codeNSS dt_codeNSS year)
egen double n_hh_exp_q12_n = mean(temp_n_hh_exp_q12_n), by(st_codeNSS dt_codeNSS year)	
egen double n_hh_exp_q34_n = mean(temp_n_hh_exp_q34_n), by(st_codeNSS dt_codeNSS year)	
drop temp*
la var n_hh_exp_q12_n "# NSS households surveyed by stdt-year (exp <=natl-yr median)"
la var n_hh_exp_q34_n "# NSS households surveyed by stdt-year (exp >natl-year median)"

	// Counts for expenditures above/below median (dist-year)
egen double temp_n_hh_exp_q12_d = count(nss) if monthly_per_capita_exp_30<=exp_d_yr_p50 , by(st_codeNSS dt_codeNSS year)	
egen double temp_n_hh_exp_q34_d = count(nss) if monthly_per_capita_exp_30>exp_d_yr_p50 , by(st_codeNSS dt_codeNSS year)
egen double n_hh_exp_q12_d = mean(temp_n_hh_exp_q12_d), by(st_codeNSS dt_codeNSS year)	
egen double n_hh_exp_q34_d = mean(temp_n_hh_exp_q34_d), by(st_codeNSS dt_codeNSS year)	
drop temp*
la var n_hh_exp_q12_d "# NSS households surveyed by stdt-year (exp <=dist-yr median)"
la var n_hh_exp_q34_d "# NSS households surveyed by stdt-year (exp >dist-year median)"

	// Counts for expenditures in quartiles (natl-year)
egen double temp_n_hh_exp_q1_n = count(nss) if monthly_per_capita_exp_30<=exp_n_yr_p25 , by(st_codeNSS dt_codeNSS year)	
egen double temp_n_hh_exp_q2_n = count(nss) if monthly_per_capita_exp_30>exp_n_yr_p25 & monthly_per_capita_exp_30<=exp_n_yr_p50, by(st_codeNSS dt_codeNSS year)	
egen double temp_n_hh_exp_q3_n = count(nss) if monthly_per_capita_exp_30>exp_n_yr_p50 & monthly_per_capita_exp_30<=exp_n_yr_p75 , by(st_codeNSS dt_codeNSS year)	
egen double temp_n_hh_exp_q4_n = count(nss) if monthly_per_capita_exp_30>exp_n_yr_p75 , by(st_codeNSS dt_codeNSS year)	
egen double n_hh_exp_q1_n = mean(temp_n_hh_exp_q1_n), by(st_codeNSS dt_codeNSS year)	
egen double n_hh_exp_q2_n = mean(temp_n_hh_exp_q2_n), by(st_codeNSS dt_codeNSS year)	
egen double n_hh_exp_q3_n = mean(temp_n_hh_exp_q3_n), by(st_codeNSS dt_codeNSS year)	
egen double n_hh_exp_q4_n = mean(temp_n_hh_exp_q4_n), by(st_codeNSS dt_codeNSS year)	
drop temp*
la var n_hh_exp_q1_n "# NSS households surveyed by stdt-year (exp in natl-yr 1st qrtle)"
la var n_hh_exp_q2_n "# NSS households surveyed by stdt-year (exp in natl-yr 2nd qrtle)"
la var n_hh_exp_q3_n "# NSS households surveyed by stdt-year (exp in natl-yr 3rd qrtle)"
la var n_hh_exp_q4_n "# NSS households surveyed by stdt-year (exp in natl-yr 4th qrtle)"

	// Counts for expenditures in quartiles (dist-year)
egen double temp_n_hh_exp_q1_d = count(nss) if monthly_per_capita_exp_30<=exp_d_yr_p25 , by(st_codeNSS dt_codeNSS year)	
egen double temp_n_hh_exp_q2_d = count(nss) if monthly_per_capita_exp_30>exp_d_yr_p25 & monthly_per_capita_exp_30<=exp_d_yr_p50, by(st_codeNSS dt_codeNSS year)	
egen double temp_n_hh_exp_q3_d = count(nss) if monthly_per_capita_exp_30>exp_d_yr_p50 & monthly_per_capita_exp_30<=exp_d_yr_p75 , by(st_codeNSS dt_codeNSS year)	
egen double temp_n_hh_exp_q4_d = count(nss) if monthly_per_capita_exp_30>exp_d_yr_p75 , by(st_codeNSS dt_codeNSS year)	
egen double n_hh_exp_q1_d = mean(temp_n_hh_exp_q1_d), by(st_codeNSS dt_codeNSS year)	
egen double n_hh_exp_q2_d = mean(temp_n_hh_exp_q2_d), by(st_codeNSS dt_codeNSS year)	
egen double n_hh_exp_q3_d = mean(temp_n_hh_exp_q3_d), by(st_codeNSS dt_codeNSS year)	
egen double n_hh_exp_q4_d = mean(temp_n_hh_exp_q4_d), by(st_codeNSS dt_codeNSS year)	
drop temp*
la var n_hh_exp_q1_d "# NSS households surveyed by stdt-year (exp in dist-yr 1st qrtle)"
la var n_hh_exp_q2_d "# NSS households surveyed by stdt-year (exp in dist-yr 2nd qrtle)"
la var n_hh_exp_q3_d "# NSS households surveyed by stdt-year (exp in dist-yr 3rd qrtle)"
la var n_hh_exp_q4_d "# NSS households surveyed by stdt-year (exp in dist-yr 4th qrtle)"

	// Counts for population above/below 2000 and expenditures above/below median (natl-year)
egen double temp_n_hh_under2k_exp_q12_n = count(nss) if frame_population<=2000 & frame_population!=. & monthly_per_capita_exp_30<=exp_n_yr_p50 , by(st_codeNSS dt_codeNSS year)	
egen double temp_n_hh_under2k_exp_q34_n = count(nss) if frame_population<=2000 & frame_population!=. & monthly_per_capita_exp_30>exp_n_yr_p50 , by(st_codeNSS dt_codeNSS year)	
egen double temp_n_hh_over2k_exp_q12_n = count(nss) if frame_population>2000 & frame_population!=. & monthly_per_capita_exp_30<=exp_n_yr_p50 , by(st_codeNSS dt_codeNSS year)	
egen double temp_n_hh_over2k_exp_q34_n = count(nss) if frame_population>2000 & frame_population!=. & monthly_per_capita_exp_30>exp_n_yr_p50 , by(st_codeNSS dt_codeNSS year)	
egen double n_hh_under2k_exp_q12_n = mean(temp_n_hh_under2k_exp_q12_n), by(st_codeNSS dt_codeNSS year)	
egen double n_hh_under2k_exp_q34_n = mean(temp_n_hh_under2k_exp_q34_n), by(st_codeNSS dt_codeNSS year)	
egen double n_hh_over2k_exp_q12_n = mean(temp_n_hh_over2k_exp_q12_n), by(st_codeNSS dt_codeNSS year)	
egen double n_hh_over2k_exp_q34_n = mean(temp_n_hh_over2k_exp_q34_n), by(st_codeNSS dt_codeNSS year)	
drop temp*
la var n_hh_under2k_exp_q12_n "# NSS households surveyed by stdt-year (2001 pop <=2000, exp <=natl-yr median)"
la var n_hh_under2k_exp_q34_n "# NSS households surveyed by stdt-year (2001 pop <=2000, exp >natl-yr median)"
la var n_hh_over2k_exp_q12_n "# NSS households surveyed by stdt-year (2001 pop >2000, exp <=natl-yr median)"
la var n_hh_over2k_exp_q34_n "# NSS households surveyed by stdt-year (2001 pop >2000, exp >natl-yr median)"

	// Counts for population above/below 2000 and expenditures above/below median (dist-year)
egen double temp_n_hh_under2k_exp_q12_d = count(nss) if frame_population<=2000 & frame_population!=. & monthly_per_capita_exp_30<=exp_d_yr_p50 , by(st_codeNSS dt_codeNSS year)	
egen double temp_n_hh_under2k_exp_q34_d = count(nss) if frame_population<=2000 & frame_population!=. & monthly_per_capita_exp_30>exp_d_yr_p50 , by(st_codeNSS dt_codeNSS year)	
egen double temp_n_hh_over2k_exp_q12_d = count(nss) if frame_population>2000 & frame_population!=. & monthly_per_capita_exp_30<=exp_d_yr_p50 , by(st_codeNSS dt_codeNSS year)	
egen double temp_n_hh_over2k_exp_q34_d = count(nss) if frame_population>2000 & frame_population!=. & monthly_per_capita_exp_30>exp_d_yr_p50 , by(st_codeNSS dt_codeNSS year)	
egen double n_hh_under2k_exp_q12_d = mean(temp_n_hh_under2k_exp_q12_d), by(st_codeNSS dt_codeNSS year)	
egen double n_hh_under2k_exp_q34_d = mean(temp_n_hh_under2k_exp_q34_d), by(st_codeNSS dt_codeNSS year)	
egen double n_hh_over2k_exp_q12_d = mean(temp_n_hh_over2k_exp_q12_d), by(st_codeNSS dt_codeNSS year)	
egen double n_hh_over2k_exp_q34_d = mean(temp_n_hh_over2k_exp_q34_d), by(st_codeNSS dt_codeNSS year)	
drop temp*
la var n_hh_under2k_exp_q12_d "# NSS households surveyed by stdt-year (2001 pop <=2000, exp <=dist-yr median)"
la var n_hh_under2k_exp_q34_d "# NSS households surveyed by stdt-year (2001 pop <=2000, exp >dist-yr median)"
la var n_hh_over2k_exp_q12_d "# NSS households surveyed by stdt-year (2001 pop >2000, exp <=dist-yr median)"
la var n_hh_over2k_exp_q34_d "# NSS households surveyed by stdt-year (2001 pop >2000, exp >dist-yr median)"

	// Counts by max(WT) quintile
egen double temp_n_hh_dec12 = count(WT) if inrange(WT_decile,1,2) , by(st_codeNSS dt_codeNSS year)	
egen double temp_n_hh_dec34 = count(WT) if inrange(WT_decile,3,4) , by(st_codeNSS dt_codeNSS year)	
egen double temp_n_hh_dec56 = count(WT) if inrange(WT_decile,5,6) , by(st_codeNSS dt_codeNSS year)	
egen double temp_n_hh_dec78 = count(WT) if inrange(WT_decile,7,8) , by(st_codeNSS dt_codeNSS year)	
egen double temp_n_hh_dec90 = count(WT) if inrange(WT_decile,9,10) , by(st_codeNSS dt_codeNSS year)	
egen double n_hh_dec12 = mean(temp_n_hh_dec12), by(st_codeNSS dt_codeNSS year)	
egen double n_hh_dec34 = mean(temp_n_hh_dec34), by(st_codeNSS dt_codeNSS year)	
egen double n_hh_dec56 = mean(temp_n_hh_dec56), by(st_codeNSS dt_codeNSS year)	
egen double n_hh_dec78 = mean(temp_n_hh_dec78), by(st_codeNSS dt_codeNSS year)	
egen double n_hh_dec90 = mean(temp_n_hh_dec90), by(st_codeNSS dt_codeNSS year)	
drop temp*
la var n_hh_dec12 "# NSS households surveyed by stdt-year (WT deciles 1-2)"
la var n_hh_dec34 "# NSS households surveyed by stdt-year (WT deciles 3-4)"
la var n_hh_dec56 "# NSS households surveyed by stdt-year (WT deciles 5-6)"
la var n_hh_dec78 "# NSS households surveyed by stdt-year (WT deciles 7-8)"
la var n_hh_dec90 "# NSS households surveyed by stdt-year (WT deciles 9-10)"

	// Counts by max(WT) quartile
forvalues i = 1(1)4 {
	egen double temp_n_hh_quart`i' = count(WT) if WT_quartile==`i' , by(st_codeNSS dt_codeNSS year)	
	egen double n_hh_quart`i' = mean(temp_n_hh_quart`i'), by(st_codeNSS dt_codeNSS year)	
	la var n_hh_quart`i' "# NSS households surveyed by stdt-year (WT quartile `i')"
}
drop temp*

	// Counts removing top max(WT) deciles one by one
forvalues i = 9(-1)3 {
	egen double temp_n_hh_dec1`i' = count(WT) if inrange(WT_decile,1,`i') , by(st_codeNSS dt_codeNSS year)
	egen double n_hh_dec1`i' = mean(temp_n_hh_dec1`i'), by(st_codeNSS dt_codeNSS year)	
	la var n_hh_dec1`i' "# NSS households surveyed by stdt-year (WT deciles 1-`i')"
}
drop temp*

	// Opposite of the above, keeping top deciles of max(WT), one by one
forvalues i = 8(-1)2 {
	egen double temp_n_hh_dec`i'0 = count(WT) if inrange(WT_decile,`i',10) , by(st_codeNSS dt_codeNSS year)
	egen double n_hh_dec`i'0 = mean(temp_n_hh_dec`i'0), by(st_codeNSS dt_codeNSS year)	
	la var n_hh_dec`i'0 "# NSS households surveyed by stdt-year (WT deciles `i'-10)"
}
drop temp*

	// Counts removing top [max(WT) deciles U dist_pop deciles] one by one
forvalues i = 9(-1)2 {
	egen double temp_n_hh_DEC1`i' = count(WT) if inrange(WT_decile,1,`i') | inrange(dist_pop_decile,1,`i') , by(st_codeNSS dt_codeNSS year)
	egen double n_hh_DEC1`i' = mean(temp_n_hh_DEC1`i'), by(st_codeNSS dt_codeNSS year)	
	la var n_hh_DEC1`i' "# NSS households surveyed by stdt-year (WT deciles 1-`i' or Dist Pop deciles 1-`i')"
}
drop temp*


	// Execute collapse for many sets of variables
rename monthly_per_capita_exp_30 mth_pc_exp
rename *_yn *
rename electricity_* elec_*
rename implied_elec_price elec_price
rename sewing_machine sewing_mach
rename elec_q elec_q_yn
rename other_fuel_value othfuel_val
gen mth_pc_expE1 = mth_pc_exp - elec_value/household_size
gen mth_pc_expE2 = mth_pc_exp - 2*(elec_value/household_size)
la var mth_pc_expE1 "Monthly exp per capita less electricity spending"
la var mth_pc_expE2 "Monthly exp per capita less electricity spending (2x)"
gen MTH_pc_exp = mth_pc_exp

foreach v of varlist mth_pc_exp - fridge elec_q_yn mth_pc_expE1 mth_pc_expE2 {
	
	// Full collapse
	egen double temp_full = sum(`v'*WT/sum_wgts), by(st_codeNSS dt_codeNSS year)
	
	// Pop under 500
	egen double TEMP_under500 = sum(`v'*WT/sum_wgts_under500) if frame_population<=500 & frame_population!=. , by(st_codeNSS dt_codeNSS year)
	egen double temp_under500 = mean(TEMP_under500), by(st_codeNSS dt_codeNSS year)
		
	// Pop over 500
	egen double TEMP_over500 = sum(`v'*WT/sum_wgts_over500) if frame_population>500 & frame_population!=. , by(st_codeNSS dt_codeNSS year)
	egen double temp_over500 = mean(TEMP_over500), by(st_codeNSS dt_codeNSS year)

	// Pop under 1k
	egen double TEMP_under1k = sum(`v'*WT/sum_wgts_under1k) if frame_population<=1000 & frame_population!=. , by(st_codeNSS dt_codeNSS year)
	egen double temp_under1k = mean(TEMP_under1k), by(st_codeNSS dt_codeNSS year)
		
	// Pop over 1k
	egen double TEMP_over1k = sum(`v'*WT/sum_wgts_over1k) if frame_population>1000 & frame_population!=. , by(st_codeNSS dt_codeNSS year)
	egen double temp_over1k = mean(TEMP_over1k), by(st_codeNSS dt_codeNSS year)
		
	// Pop under 2k
	egen double TEMP_under2k = sum(`v'*WT/sum_wgts_under2k) if frame_population<=2000 & frame_population!=. , by(st_codeNSS dt_codeNSS year)
	egen double temp_under2k = mean(TEMP_under2k), by(st_codeNSS dt_codeNSS year)
		
	// Pop over 2k
	egen double TEMP_over2k = sum(`v'*WT/sum_wgts_over2k) if frame_population>2000 & frame_population!=. , by(st_codeNSS dt_codeNSS year)
	egen double temp_over2k = mean(TEMP_over2k), by(st_codeNSS dt_codeNSS year)

	// Pop under 4k
	egen double TEMP_under4k = sum(`v'*WT/sum_wgts_under4k) if frame_population<=4000 & frame_population!=. , by(st_codeNSS dt_codeNSS year)
	egen double temp_under4k = mean(TEMP_under4k), by(st_codeNSS dt_codeNSS year)
		
	// Pop over 4k
	egen double TEMP_over4k = sum(`v'*WT/sum_wgts_over4k) if frame_population>4000 & frame_population!=. , by(st_codeNSS dt_codeNSS year)
	egen double temp_over4k = mean(TEMP_over4k), by(st_codeNSS dt_codeNSS year)
	
	// Pop btw 1k and 2k
	egen double TEMP_1kto2k = sum(`v'*WT/sum_wgts_1kto2k) if frame_population>1000 & frame_population<=2000 & frame_population!=. , by(st_codeNSS dt_codeNSS year)
	egen double temp_1kto2k = mean(TEMP_1kto2k), by(st_codeNSS dt_codeNSS year)
	
	// Pop btw 2k and 4k
	egen double TEMP_2kto4k = sum(`v'*WT/sum_wgts_2kto4k) if frame_population>2000 & frame_population<=4000 & frame_population!=. , by(st_codeNSS dt_codeNSS year)
	egen double temp_2kto4k = mean(TEMP_2kto4k), by(st_codeNSS dt_codeNSS year)
	
	// Exp below median (natl, year)
	egen double TEMP_exp_q12_n = sum(`v'*WT/sum_wgts_exp_q12_n) if MTH_pc_exp<=exp_n_yr_p50 , by(st_codeNSS dt_codeNSS year)
	egen double temp_exp_q12n = mean(TEMP_exp_q12_n), by(st_codeNSS dt_codeNSS year)
	
	// Exp above median (natl, year)
	egen double TEMP_exp_q34_n = sum(`v'*WT/sum_wgts_exp_q34_n) if MTH_pc_exp>exp_n_yr_p50 , by(st_codeNSS dt_codeNSS year)
	egen double temp_exp_q34n = mean(TEMP_exp_q34_n), by(st_codeNSS dt_codeNSS year)
	
	// Exp in Q1 (natl, year)
	egen double TEMP_exp_q1_n = sum(`v'*WT/sum_wgts_exp_q1_n) if MTH_pc_exp<=exp_n_yr_p25 , by(st_codeNSS dt_codeNSS year)
	egen double temp_exp_q1n = mean(TEMP_exp_q1_n), by(st_codeNSS dt_codeNSS year)

	// Exp in Q2 (natl, year)
	egen double TEMP_exp_q2_n = sum(`v'*WT/sum_wgts_exp_q2_n) if MTH_pc_exp>exp_n_yr_p25 & MTH_pc_exp<=exp_n_yr_p50 , by(st_codeNSS dt_codeNSS year)
	egen double temp_exp_q2n = mean(TEMP_exp_q2_n), by(st_codeNSS dt_codeNSS year)

	// Exp in Q3 (natl, year)
	egen double TEMP_exp_q3_n = sum(`v'*WT/sum_wgts_exp_q3_n) if MTH_pc_exp>exp_n_yr_p50 & MTH_pc_exp<=exp_n_yr_p75 , by(st_codeNSS dt_codeNSS year)
	egen double temp_exp_q3n = mean(TEMP_exp_q3_n), by(st_codeNSS dt_codeNSS year)
	
	// Exp in Q4 (natl, year)
	egen double TEMP_exp_q4_n = sum(`v'*WT/sum_wgts_exp_q4_n) if MTH_pc_exp>exp_n_yr_p75 , by(st_codeNSS dt_codeNSS year)
	egen double temp_exp_q4n = mean(TEMP_exp_q4_n), by(st_codeNSS dt_codeNSS year)
	
	// Pop under 2k & Exp below median (natl, year)
	egen double TEMP_under2k_exp_q12_n = sum(`v'*WT/sum_wgts_under2k_exp_q12_n) if frame_population<=2000 & frame_population!=. & MTH_pc_exp<=exp_n_yr_p50 , by(st_codeNSS dt_codeNSS year)
	egen double temp_under2k_exp_q12n = mean(TEMP_under2k_exp_q12_n), by(st_codeNSS dt_codeNSS year)

	// Pop under 2k & Exp above median (natl, year)
	egen double TEMP_under2k_exp_q34_n = sum(`v'*WT/sum_wgts_under2k_exp_q34_n) if frame_population<=2000 & frame_population!=. & MTH_pc_exp>exp_n_yr_p50 , by(st_codeNSS dt_codeNSS year)
	egen double temp_under2k_exp_q34n = mean(TEMP_under2k_exp_q34_n), by(st_codeNSS dt_codeNSS year)

	// Pop over 2k & Exp below median (natl, year)
	egen double TEMP_over2k_exp_q12_n = sum(`v'*WT/sum_wgts_over2k_exp_q12_n) if frame_population>2000 & frame_population!=. & MTH_pc_exp<=exp_n_yr_p50 , by(st_codeNSS dt_codeNSS year)
	egen double temp_over2k_exp_q12n = mean(TEMP_over2k_exp_q12_n), by(st_codeNSS dt_codeNSS year)

	// Pop over 2k & Exp above median (natl, year)
	egen double TEMP_over2k_exp_q34_n = sum(`v'*WT/sum_wgts_over2k_exp_q34_n) if frame_population>2000 & frame_population!=. & MTH_pc_exp>exp_n_yr_p50 , by(st_codeNSS dt_codeNSS year)
	egen double temp_over2k_exp_q34n = mean(TEMP_over2k_exp_q34_n), by(st_codeNSS dt_codeNSS year)

	// Exp below median (dist, year)
	egen double TEMP_exp_q12_d = sum(`v'*WT/sum_wgts_exp_q12_d) if MTH_pc_exp<=exp_d_yr_p50 , by(st_codeNSS dt_codeNSS year)
	egen double temp_exp_q12d = mean(TEMP_exp_q12_d), by(st_codeNSS dt_codeNSS year)
	
	// Exp above median (dist, year)
	egen double TEMP_exp_q34_d = sum(`v'*WT/sum_wgts_exp_q34_d) if MTH_pc_exp>exp_d_yr_p50 , by(st_codeNSS dt_codeNSS year)
	egen double temp_exp_q34d = mean(TEMP_exp_q34_d), by(st_codeNSS dt_codeNSS year)
	
	// Exp in Q1 (dist, year)
	egen double TEMP_exp_q1_d = sum(`v'*WT/sum_wgts_exp_q1_d) if MTH_pc_exp<=exp_d_yr_p25 , by(st_codeNSS dt_codeNSS year)
	egen double temp_exp_q1d = mean(TEMP_exp_q1_d), by(st_codeNSS dt_codeNSS year)

	// Exp in Q2 (dist, year)
	egen double TEMP_exp_q2_d = sum(`v'*WT/sum_wgts_exp_q2_d) if MTH_pc_exp>exp_d_yr_p25 & MTH_pc_exp<=exp_d_yr_p50 , by(st_codeNSS dt_codeNSS year)
	egen double temp_exp_q2d = mean(TEMP_exp_q2_d), by(st_codeNSS dt_codeNSS year)

	// Exp in Q3 (dist, year)
	egen double TEMP_exp_q3_d = sum(`v'*WT/sum_wgts_exp_q3_d) if MTH_pc_exp>exp_d_yr_p50 & MTH_pc_exp<=exp_d_yr_p75 , by(st_codeNSS dt_codeNSS year)
	egen double temp_exp_q3d = mean(TEMP_exp_q3_d), by(st_codeNSS dt_codeNSS year)
	
	// Exp in Q4 (dist, year)
	egen double TEMP_exp_q4_d = sum(`v'*WT/sum_wgts_exp_q4_d) if MTH_pc_exp>exp_d_yr_p75 , by(st_codeNSS dt_codeNSS year)
	egen double temp_exp_q4d = mean(TEMP_exp_q4_d), by(st_codeNSS dt_codeNSS year)
	
	// Pop under 2k & Exp below median (dist, year)
	egen double TEMP_under2k_exp_q12_d = sum(`v'*WT/sum_wgts_under2k_exp_q12_d) if frame_population<=2000 & frame_population!=. & MTH_pc_exp<=exp_d_yr_p50 , by(st_codeNSS dt_codeNSS year)
	egen double temp_under2k_exp_q12d = mean(TEMP_under2k_exp_q12_d), by(st_codeNSS dt_codeNSS year)

	// Pop under 2k & Exp above median (dist, year)
	egen double TEMP_under2k_exp_q34_d = sum(`v'*WT/sum_wgts_under2k_exp_q34_d) if frame_population<=2000 & frame_population!=. & MTH_pc_exp>exp_d_yr_p50 , by(st_codeNSS dt_codeNSS year)
	egen double temp_under2k_exp_q34d = mean(TEMP_under2k_exp_q34_d), by(st_codeNSS dt_codeNSS year)

	// Pop over 2k & Exp below median (dist, year)
	egen double TEMP_over2k_exp_q12_d = sum(`v'*WT/sum_wgts_over2k_exp_q12_d) if frame_population>2000 & frame_population!=. & MTH_pc_exp<=exp_d_yr_p50 , by(st_codeNSS dt_codeNSS year)
	egen double temp_over2k_exp_q12d = mean(TEMP_over2k_exp_q12_d), by(st_codeNSS dt_codeNSS year)

	// Pop over 2k & Exp above median (dist, year)
	egen double TEMP_over2k_exp_q34_d = sum(`v'*WT/sum_wgts_over2k_exp_q34_d) if frame_population>2000 & frame_population!=. & MTH_pc_exp>exp_d_yr_p50 , by(st_codeNSS dt_codeNSS year)
	egen double temp_over2k_exp_q34d = mean(TEMP_over2k_exp_q34_d), by(st_codeNSS dt_codeNSS year)
	
	// max(WT) quintile
	egen double TEMP_dec12 = sum(`v'*WT/sum_wgts_dec12) if inrange(WT_decile,1,2) , by(st_codeNSS dt_codeNSS year)	
	egen double TEMP_dec34 = sum(`v'*WT/sum_wgts_dec34) if inrange(WT_decile,3,4) , by(st_codeNSS dt_codeNSS year)	
	egen double TEMP_dec56 = sum(`v'*WT/sum_wgts_dec56) if inrange(WT_decile,5,6) , by(st_codeNSS dt_codeNSS year)	
	egen double TEMP_dec78 = sum(`v'*WT/sum_wgts_dec78) if inrange(WT_decile,7,8) , by(st_codeNSS dt_codeNSS year)	
	egen double TEMP_dec90 = sum(`v'*WT/sum_wgts_dec90) if inrange(WT_decile,9,10) , by(st_codeNSS dt_codeNSS year)	
	egen double temp_dec12 = mean(TEMP_dec12), by(st_codeNSS dt_codeNSS year)	
	egen double temp_dec34 = mean(TEMP_dec34), by(st_codeNSS dt_codeNSS year)	
	egen double temp_dec56 = mean(TEMP_dec56), by(st_codeNSS dt_codeNSS year)	
	egen double temp_dec78 = mean(TEMP_dec78), by(st_codeNSS dt_codeNSS year)	
	egen double temp_dec90 = mean(TEMP_dec90), by(st_codeNSS dt_codeNSS year)	

	// max(WT) quartile
	forvalues i = 1(1)4 {
		egen double TEMP_quart`i' = sum(`v'*WT/sum_wgts_quart`i') if WT_quartile==`i', by(st_codeNSS dt_codeNSS year)	
		egen double temp_quart`i' = mean(TEMP_quart`i'), by(st_codeNSS dt_codeNSS year)	
	}

	// removing top max(WT) deciles one by one
	forvalues i = 9(-1)3 {
		egen double TEMP_dec1`i' = sum(`v'*WT/sum_wgts_dec1`i') if inrange(WT_decile,1,`i') , by(st_codeNSS dt_codeNSS year)
		egen double temp_dec1`i' = mean(TEMP_dec1`i'), by(st_codeNSS dt_codeNSS year)	
	}

	// Opposite of the above, keeping top deciles of max(WT), one by one
	forvalues i = 8(-1)2 {
		egen double TEMP_dec`i'0 = sum(`v'*WT/sum_wgts_dec`i'0) if inrange(WT_decile,`i',10) , by(st_codeNSS dt_codeNSS year)
		egen double temp_dec`i'0 = mean(TEMP_dec`i'0), by(st_codeNSS dt_codeNSS year)	
	}

	// removing top [max(WT) deciles U dist_pop deciles] one by one
	forvalues i = 9(-1)2 {
		egen double TEMP_DEC1`i' =  sum(`v'*WT/sum_wgts_DEC1`i') if inrange(WT_decile,1,`i') | inrange(dist_pop_decile,1,`i') , by(st_codeNSS dt_codeNSS year)
		egen double temp_DEC1`i' = mean(TEMP_DEC1`i'), by(st_codeNSS dt_codeNSS year)	
	}

	
	
	// Store variables
	replace `v' = temp_full
	drop temp_full
	rename temp_* `v'_*

	// Attach labels
	local lab : variable label `v'
	la var `v'_under500 "`v' (2001 pop <=500)"
	la var `v'_over500 "`v' (2001 pop >500)"
	la var `v'_under1k "`v' (2001 pop <=1000)"
	la var `v'_over1k "`v' (2001 pop >1000)"
	la var `v'_under2k "`v' (2001 pop <=2000)"
	la var `v'_over2k "`v' (2001 pop >2000)"
	la var `v'_under4k "`v' (2001 pop <=4000)"
	la var `v'_over4k "`v' (2001 pop >4000)"
	la var `v'_1kto2k "`v' (2001 pop (1000,2000])"
	la var `v'_2kto4k "`v' (2001 pop (2000,4000])"
	la var `v'_exp_q12n "`v' (exp <=natl-yr median)"
	la var `v'_exp_q34n "`v' (exp >natl-yr median)"
	la var `v'_exp_q12d "`v' (exp <=dist-yr median)"
	la var `v'_exp_q34d "`v' (exp >dist-yr median)"
	la var `v'_exp_q1n "`v' (exp in natl-yr 1st qrtle)"
	la var `v'_exp_q2n "`v' (exp in natl-yr 2nd qrtle)"
	la var `v'_exp_q3n "`v' (exp in natl-yr 3rd qrtle)"
	la var `v'_exp_q4n "`v' (exp in natl-yr 4th qrtle)"
	la var `v'_exp_q1d "`v' (exp in dist-yr 1st qrtle)"
	la var `v'_exp_q2d "`v' (exp in dist-yr 2nd qrtle)"
	la var `v'_exp_q3d "`v' (exp in dist-yr 3rd qrtle)"
	la var `v'_exp_q4d "`v' (exp in dist-yr 4th qrtle)"	
	la var `v'_under2k_exp_q12n "`v' (2001 pop <=2000, exp <=natl-yr median)"
	la var `v'_under2k_exp_q34n "`v' (2001 pop >2000, exp >natl-yr median)"
	la var `v'_over2k_exp_q12n "`v' (2001 pop <=2000, exp <=natl-yr median)"
	la var `v'_over2k_exp_q34n "`v' (2001 pop >2000, exp >natl-yr median)"		
	la var `v'_under2k_exp_q12d "`v' (2001 pop <=2000, exp <=dist-yr median)"
	la var `v'_under2k_exp_q34d "`v' (2001 pop >2000, exp >dist-yr median)"
	la var `v'_over2k_exp_q12d "`v' (2001 pop <=2000, exp <=dist-yr median)"
	la var `v'_over2k_exp_q34d "`v' (2001 pop >2000, exp >dist-yr median)"
	la var `v'_dec12 "`v' (WT deciles 1-2)"
	la var `v'_dec34 "`v' (WT deciles 3-4)"
	la var `v'_dec56 "`v' (WT deciles 5-6)"
	la var `v'_dec78 "`v' (WT deciles 7-8)"
	la var `v'_dec90 "`v' (WT deciles 9-10)"
	forvalues i = 1(1)4 {
		la var `v'_quart`i' "`v' (WT quartile 1)"
	}
	forvalues i = 9(-1)2 {
		la var `v'_dec1`i' "`v' (WT deciles 1-`i')"
		la var `v'_dec`i'0 "`v' (WT deciles `i'-10)"
		la var `v'_DEC1`i' "`v' (WT deciles 1-`i' or Dist Pop deciles 1-`i')"
	}
		
	// Drop temp variables
	drop TEMP*
}


	// Collapse to state-district-year level
drop nss nsc mult mlt multiplier wgt* WT frame_population approx_present_pop nr_of_hamlet_groups_d fsu_serial_no ///
	MTH_pc_exp stdt WT_max WT_decile pop_decile WT_quartile pop_quartile household_size
duplicates drop
unique st_codeNSS dt_codeNSS year
assert r(unique)==r(N)

	// Assess coverage
sort st_codeNSS dt_codeNSS year
unique st_codeNSS dt_codeNSS	
duplicates t st_codeNSS dt_codeNSS, gen(dup)
unique st_codeNSS dt_codeNSS if dup==2
unique st_codeNSS dt_codeNSS if dup==1
unique st_codeNSS dt_codeNSS if dup==0
unique st_codeNSS dt_codeNSS if dup>0 & year==2010
egen temp_2000 = max(year==2000), by(st_codeNSS dt_codeNSS) 
egen temp_2005 = max(year==2005), by(st_codeNSS dt_codeNSS) 
egen temp_2010 = max(year==2010), by(st_codeNSS dt_codeNSS) 
unique st_codeNSS dt_codeNSS if dup>0 & temp_2010==0
unique st_codeNSS dt_codeNSS if dup>0 & temp_2005==0
unique st_codeNSS dt_codeNSS if dup>0 & temp_2000==0
drop temp* dup

	// Populate zeros where missing (small populations)
foreach v of varlist n_hh_under* {
	assert `v'!=0
	replace `v'= 0 if `v'==. & year>2000
}
tab n_hh_under500 if year==2005 // 43% zeros
tab n_hh_under500 if year==2010 // 50% zeros
tab n_hh_under1k if year==2005 // 13% zeros
tab n_hh_under1k if year==2010 // 17% zeros
tab n_hh_under2k if year==2005 // 3% zeros
tab n_hh_under2k if year==2010 // 2% zeros
tab n_hh_under4k if year==2005 // 1% zeros
tab n_hh_under4k if year==2010 // 1% zeros
tab n_hh_under2k_exp_q12_n if year==2005 // 5% zeros
tab n_hh_under2k_exp_q12_n if year==2010 // 7% zeros
tab n_hh_under2k_exp_q34_n if year==2005 // 3% zeros
tab n_hh_under2k_exp_q34_n if year==2010 // 4% zeros
tab n_hh_under2k_exp_q12_d if year==2005 // 3% zeros
tab n_hh_under2k_exp_q12_d if year==2010 // 4% zeros
tab n_hh_under2k_exp_q34_d if year==2005 // 3% zeros
tab n_hh_under2k_exp_q34_d if year==2010 // 3% zeros

	// Populate zeros where missing (deciles)
foreach v of varlist n_hh_dec* n_hh_DEC* {
	assert `v'!=0
	replace `v'= 0 if `v'==. 
}
tab n_hh_dec90 if year==2000 // 44% zeros
tab n_hh_dec90 if year==2005 // 46% zeros
tab n_hh_dec90 if year==2010 // 47% zeros
tab n_hh_dec78 if year==2000 // 34% zeros
tab n_hh_dec78 if year==2005 // 34% zeros
tab n_hh_dec78 if year==2010 // 34% zeros
tab n_hh_dec56 if year==2000 // 36% zeros
tab n_hh_dec56 if year==2005 // 32% zeros
tab n_hh_dec56 if year==2010 // 29% zeros
tab n_hh_dec34 if year==2000 // 45% zeros
tab n_hh_dec34 if year==2005 // 44% zeros
tab n_hh_dec34 if year==2010 // 37% zeros

tab n_hh_dec12 if year==2000 // 54% zeros
tab n_hh_dec12 if year==2005 // 72% zeros
tab n_hh_dec12 if year==2010 // 65% zeros
tab n_hh_dec13 if year==2000 // 37% zeros
tab n_hh_dec13 if year==2005 // 50% zeros
tab n_hh_dec13 if year==2010 // 41% zeros
tab n_hh_dec14 if year==2000 // 26% zeros
tab n_hh_dec14 if year==2005 // 30% zeros
tab n_hh_dec14 if year==2010 // 25% zeros
tab n_hh_dec15 if year==2000 // 17% zeros
tab n_hh_dec15 if year==2005 // 18% zeros
tab n_hh_dec15 if year==2010 // 14% zeros
tab n_hh_dec16 if year==2000 // 10% zeros
tab n_hh_dec16 if year==2005 // 10% zeros
tab n_hh_dec16 if year==2010 // 7% zeros
tab n_hh_dec17 if year==2000 // 6% zeros
tab n_hh_dec17 if year==2005 // 4% zeros
tab n_hh_dec17 if year==2010 // 2% zeros
tab n_hh_dec18 if year==2000 // 2% zeros
tab n_hh_dec18 if year==2005 // 2% zeros
tab n_hh_dec18 if year==2010 // 1% zeros
tab n_hh_dec19 if year==2000 // 1% zeros
tab n_hh_dec19 if year==2005 // 1% zeros
tab n_hh_dec19 if year==2010 // 0% zeros

tab n_hh_DEC12 if year==2000 // 52% zeros
tab n_hh_DEC12 if year==2005 // 67% zeros
tab n_hh_DEC12 if year==2010 // 61% zeros
tab n_hh_DEC13 if year==2000 // 34% zeros
tab n_hh_DEC13 if year==2005 // 43% zeros
tab n_hh_DEC13 if year==2010 // 37% zeros
tab n_hh_DEC14 if year==2000 // 20% zeros
tab n_hh_DEC14 if year==2005 // 24% zeros
tab n_hh_DEC14 if year==2010 // 22% zeros
tab n_hh_DEC15 if year==2000 // 11% zeros
tab n_hh_DEC15 if year==2005 // 13% zeros
tab n_hh_DEC15 if year==2010 // 11% zeros
tab n_hh_DEC16 if year==2000 // 5% zeros
tab n_hh_DEC16 if year==2005 // 6% zeros
tab n_hh_DEC16 if year==2010 // 4% zeros
tab n_hh_DEC17 if year==2000 // 2% zeros
tab n_hh_DEC17 if year==2005 // 2% zeros
tab n_hh_DEC17 if year==2010 // 2% zeros
tab n_hh_DEC18 if year==2000 // 1% zeros
tab n_hh_DEC18 if year==2005 // 1% zeros
tab n_hh_DEC18 if year==2010 // 0% zeros
tab n_hh_DEC19 if year==2000 // 0% zeros
tab n_hh_DEC19 if year==2005 // 0% zeros
tab n_hh_DEC19 if year==2010 // 0% zeros

	// Populate zeros where missing (quartiles)
foreach v of varlist n_hh_quart* {
	assert `v'!=0
	replace `v'= 0 if `v'==. 
}
tab n_hh_quart4 if year==2000 // 39% zeros
tab n_hh_quart4 if year==2005 // 41% zeros
tab n_hh_quart4 if year==2010 // 42% zeros
tab n_hh_quart3 if year==2000 // 30% zeros
tab n_hh_quart3 if year==2005 // 30% zeros
tab n_hh_quart3 if year==2010 // 29% zeros
tab n_hh_quart2 if year==2000 // 37% zeros
tab n_hh_quart2 if year==2005 // 34% zeros
tab n_hh_quart2 if year==2010 // 30% zeros
tab n_hh_quart1 if year==2000 // 45% zeros
tab n_hh_quart1 if year==2005 // 59% zeros
tab n_hh_quart1 if year==2010 // 52% zeros


	// some data checks
correlate elec_q_yn elec_light if year==2000	
correlate elec_q_yn elec_light if year==2005
correlate elec_q_yn elec_light if year==2010
correlate elec_q_yn fan if year==2000	
correlate elec_q_yn fan if year==2005
correlate elec_q_yn fan if year==2010
correlate elec_light fan if year==2000	
correlate elec_light fan if year==2005
correlate elec_light fan if year==2010
correlate elec_light tv if year==2000	
correlate elec_light tv if year==2005
correlate elec_light tv if year==2010
correlate elec_light ac if year==2000	
correlate elec_light ac if year==2005
correlate elec_light ac if year==2010
correlate elec_q_yn ac if year==2000	
correlate elec_q_yn ac if year==2005
correlate elec_q_yn ac if year==2010	
twoway (scatter elec_quantity tv if year==2000) (scatter elec_quantity tv if year==2005) 
twoway (scatter elec_quantity tv if year==2010)
twoway (scatter elec_q_yn tv if year==2000) (scatter elec_q_yn tv if year==2005) 
twoway (scatter elec_q_yn tv if year==2010)
twoway (scatter elec_q_yn elec_light if year==2010)

twoway (scatter elec_q_yn tv if year==2010), title(All households)
twoway (scatter elec_q_yn_under2k tv_under2k if year==2010), title(2001 Populaiton <=2000)
twoway (scatter elec_q_yn_under1k tv_under1k if year==2010), title(2001 Populaiton <=2000)
twoway (scatter elec_q_yn_under500 tv_under500 if year==2010), title(2001 Populaiton <=500)
twoway (scatter elec_q_yn_exp_q12n tv_exp_q12n if year==2010), title(Below-median expenditures)
twoway (scatter elec_q_yn_exp_q34n tv_exp_q34n if year==2010), title(Above-median expenditures)
twoway (scatter elec_q_yn_under2k_exp_q12n tv_under2k_exp_q12n if year==2010), title(2001 population <=2000; below-median expenditures)
twoway (scatter elec_q_yn_under2k_exp_q34n tv_under2k_exp_q34n if year==2010), title(2001 population <=2000; above-median expenditures)

tabstat elec_quantity, by(year) s(p10 p25 p50 p75 p90)

tabstat mth_pc_exp, by(year) s(min p5 p10 p25 p50 p75 p90 p95 max)
tabstat mth_pc_exp_under500, by(year) s(min p5 p10 p25 p50 p75 p90 p95 max)
tabstat mth_pc_exp_over500, by(year) s(min p5 p10 p25 p50 p75 p90 p95 max)
tabstat mth_pc_exp_under1k, by(year) s(min p5 p10 p25 p50 p75 p90 p95 max)
tabstat mth_pc_exp_over1k, by(year) s(min p5 p10 p25 p50 p75 p90 p95 max)
twoway ///
	(kdensity mth_pc_exp if year==2000) ///
	(kdensity mth_pc_exp if year==2005) ///
	(kdensity mth_pc_exp if year==2010) ///
	, legend(order(1 "2000" 2 "2005" 3 "2010"))
twoway ///
	(kdensity mth_pc_exp_under500 if year==2005 & mth_pc_exp_under1k<2000) ///
	(kdensity mth_pc_exp_over500 if year==2005 & mth_pc_exp_over1k<2000) ///
	(kdensity mth_pc_exp_under500 if year==2010 & mth_pc_exp_under1k<2000) ///
	(kdensity mth_pc_exp_over500 if year==2010 & mth_pc_exp_over1k<2000) ///
	, legend(order(1 "2005 <500" 2 "2005 >500" 3 "2010 <500" 4 "2010 >500"))
twoway ///
	(kdensity mth_pc_exp_under1k if year==2005 & mth_pc_exp_under1k<3000) ///
	(kdensity mth_pc_exp_over1k if year==2005 & mth_pc_exp_over1k<3000) ///
	(kdensity mth_pc_exp_under1k if year==2010 & mth_pc_exp_under1k<3000) ///
	(kdensity mth_pc_exp_over1k if year==2010 & mth_pc_exp_over1k<3000) ///
	, legend(order(1 "2005 <1k" 2 "2005 >1k" 3 "2010 <1k" 4 "2010 >1k"))

twoway ///
	(kdensity mth_pc_exp if year==2000, lp(-)) ///
	(kdensity mth_pc_exp_dec15 if year==2000) ///
	, legend(order(1 "2000 all" 2 "2000 dec15"))

twoway ///
	(kdensity mth_pc_exp if year==2005, lp(-)) ///
	(kdensity mth_pc_exp_dec15 if year==2005) ///
	, legend(order(1 "2005 all" 2 "2005 dec15"))

twoway ///
	(kdensity mth_pc_exp if year==2010, lp(-)) ///
	(kdensity mth_pc_exp_dec15 if year==2010) ///
	, legend(order(1 "2010 all" 2 "2010 dec15"))

twoway ///
	(kdensity mth_pc_exp if year==2000, lp(-)) ///
	(kdensity mth_pc_exp_dec13 if year==2000) ///
	, legend(order(1 "2000 all" 2 "2000 dec13"))

twoway ///
	(kdensity mth_pc_exp if year==2005, lp(-)) ///
	(kdensity mth_pc_exp_dec13 if year==2005) ///
	, legend(order(1 "2005 all" 2 "2005 dec13"))

twoway ///
	(kdensity mth_pc_exp if year==2010, lp(-)) ///
	(kdensity mth_pc_exp_dec13 if year==2010) ///
	, legend(order(1 "2010 all" 2 "2010 dec13"))


	
tabstat elec_quantity, by(year) s(min p5 p10 p25 p50 p75 p90 p95 max)
tabstat elec_quantity_under500, by(year) s(min p5 p10 p25 p50 p75 p90 p95 max)
tabstat elec_quantity_over500, by(year) s(min p5 p10 p25 p50 p75 p90 p95 max)
tabstat elec_quantity_under1k, by(year) s(min p5 p10 p25 p50 p75 p90 p95 max)
tabstat elec_quantity_over1k, by(year) s(min p5 p10 p25 p50 p75 p90 p95 max)
twoway ///
	(kdensity elec_quantity if year==2000) ///
	(kdensity elec_quantity if year==2005) ///
	(kdensity elec_quantity if year==2010) ///
	, legend(order(1 "2000" 2 "2005" 3 "2010"))
twoway ///
	(kdensity elec_quantity_under500 if year==2005 & elec_quantity_under500<100) ///
	(kdensity elec_quantity_over500 if year==2005 & elec_quantity_over500<100) ///
	(kdensity elec_quantity_under500 if year==2010 & elec_quantity_under500<100) ///
	(kdensity elec_quantity_over500 if year==2010 & elec_quantity_over500<100) ///
	, legend(order(1 "2005 <500" 2 "2005 >500" 3 "2010 <500" 4 "2010 >500"))
twoway ///
	(kdensity elec_quantity_under1k if year==2005) ///
	(kdensity elec_quantity_over1k if year==2005) ///
	(kdensity elec_quantity_under1k if year==2010) ///
	(kdensity elec_quantity_over1k if year==2010) ///
	, legend(order(1 "2005 <1k" 2 "2005 >1k" 3 "2010 <1k" 4 "2010 >1k"))

gen log_exp30 = log(mth_pc_exp)
twoway ///
	(kdensity log_exp30 if year==2000) ///
	(kdensity log_exp30 if year==2005) ///
	(kdensity log_exp30 if year==2010) ///
	, legend(order(1 "2000" 2 "2005" 3 "2010"))

gen log_elec_q = log(elec_quantity)
twoway ///
	(kdensity log_elec_q if year==2000) ///
	(kdensity log_elec_q if year==2005) ///
	(kdensity log_elec_q if year==2010) ///
	, legend(order(1 "2000" 2 "2005" 3 "2010"))
drop log*	

tabstat elec_q_yn, by(year) s(min p5 p10 p25 p50 p75 p90 p95 max)
tabstat elec_q_yn_under500, by(year) s(min p5 p10 p25 p50 p75 p90 p95 max)
tabstat elec_q_yn_over500, by(year) s(min p5 p10 p25 p50 p75 p90 p95 max)
tabstat elec_q_yn_under1k, by(year) s(min p5 p10 p25 p50 p75 p90 p95 max)
tabstat elec_q_yn_over1k, by(year) s(min p5 p10 p25 p50 p75 p90 p95 max)
twoway ///
	(kdensity elec_q_yn_under500 if year==2005) ///
	(kdensity elec_q_yn_over500 if year==2005) ///
	(kdensity elec_q_yn_under500 if year==2010) ///
	(kdensity elec_q_yn_over500 if year==2010) ///
	, legend(order(1 "2005 <500" 2 "2005 >500" 3 "2010 <500" 4 "2010 >500"))
twoway ///
	(kdensity elec_q_yn_under1k if year==2005) ///
	(kdensity elec_q_yn_over1k if year==2005) ///
	(kdensity elec_q_yn_under1k if year==2010) ///
	(kdensity elec_q_yn_over1k if year==2010) ///
	, legend(order(1 "2005 <1000" 2 "2005 >1000" 3 "2010 <1000" 4 "2010 >1000"))

twoway ///
	(kdensity elec_q_yn_dec12 if year==2000) ///
	(kdensity elec_q_yn_dec34 if year==2000) ///
	(kdensity elec_q_yn_dec56 if year==2000) ///
	(kdensity elec_q_yn_dec78 if year==2000) ///
	(kdensity elec_q_yn_dec90 if year==2000) ///
	, legend(order(1 "2000 dec12" 2 "2000 dec34" 3 "2000 dec56" 4 "2000 dec78" 5 "2000 dec90"))

twoway ///
	(kdensity elec_q_yn_dec12 if year==2005) ///
	(kdensity elec_q_yn_dec34 if year==2005) ///
	(kdensity elec_q_yn_dec56 if year==2005) ///
	(kdensity elec_q_yn_dec78 if year==2005) ///
	(kdensity elec_q_yn_dec90 if year==2005) ///
	, legend(order(1 "2005 dec12" 2 "2005 dec34" 3 "2005 dec56" 4 "2005 dec78" 5 "2005 dec90"))

twoway ///
	(kdensity elec_q_yn_dec12 if year==2010) ///
	(kdensity elec_q_yn_dec34 if year==2010) ///
	(kdensity elec_q_yn_dec56 if year==2010) ///
	(kdensity elec_q_yn_dec78 if year==2010) ///
	(kdensity elec_q_yn_dec90 if year==2010) ///
	, legend(order(1 "2010 dec12" 2 "2010 dec34" 3 "2010 dec56" 4 "2010 dec78" 5 "2010 dec90"))
	
	
	// save
sort st_codeNSS dt_codeNSS year
unique st_codeNSS dt_codeNSS year 
assert r(unique)==r(N)
compress
save "$nss/nss_hhlevel_collapsed_nss_codes.dta", replace


}	   
	   
********************************************************************************
********************************************************************************	   

** Step 3: Use xwalk to assign correct, consistent 2001 district codes (collapsed)
{
	// Merge collapsed panel into xwalk
use "$nss/nss_hhlevel_collapsed_nss_codes.dta", clear
merge 1:m st_codeNSS dt_codeNSS year using "$nss/nss_xwalk_2001codes.dta"
assert _merge==3 
drop _merge
sort year st_codeNSS dt_codeNSS
br year st_codeNSS dt_codeNSS st_code dt_code dup91

	// Diagnose duplicates
duplicates t st_codeNSS dt_codeNSS year, gen(dup91_test)
assert dup91==dup91_test if year==2000
duplicates t st_code dt_code year, gen(dup01)
tab dup01 if dt_code==.
assert dup01==0 if dt_code!=. | year>2000

	// Flag district splits
gen temp = dup91>0 & year==2000
egen flag_91dist_split = max(temp), by(st_code dt_code)
la var flag_91dist_split "Flag for 1991 district splits, requiring 2000 NSS splits"
unique st_code dt_code
local uniq = r(unique)
unique st_code dt_code if flag_91dist_split
di r(unique)/`uniq' // 35% of districts
drop temp

	// Populate flag for states with iffy 1991 disctrict matches
egen temp = max(flag_91_match_iffy), by(st_code dt_code)
replace flag_91_match_iffy = temp if flag_91_match_iffy==.
drop temp

	// Collapse to 2001 state/district codes
drop st_codeNSS dt_codeNSS sum_wgt_combined dup*
duplicates drop
drop if dt_code==.
unique st_code dt_code year
assert r(unique)==r(N)

	// Save
order st_code dt_code year
sort st_code dt_code year
compress
save "$nss/nss_hhlevel_collapsed.dta", replace
}

********************************************************************************
********************************************************************************

** Step 4: Use xwalk to assign correct, consistent 2001 district codes (uncollapsed)
{
	// Merge uncollapsed panel into xwalk
use "$nss/nss_hhlevel_uncollapsed_nss_codes.dta", clear
gen nss_hh_id = _n
joinby st_codeNSS dt_codeNSS year using "$nss/nss_xwalk_2001codes.dta", unmatched(both)
assert _merge==3 
drop _merge
sort nss_hh_id
br year st_codeNSS dt_codeNSS st_code dt_code dup91

	// Diagnose duplicates
duplicates t nss_hh_id, gen(dup91_test)
assert dup91==dup91_test if year==2000
duplicates t nss_hh_id, gen(dup01)
assert dup01==0 if year>2000
tab dup01 if dt_code==.
tab dup01 if dt_code!=.
br nss_hh_id year st_codeNSS dt_codeNSS st_code dt_code dup91 dup01 if dup01>0 & year==2000

	// Flag district splits
gen temp = dup91>0 & year==2000
egen flag_91dist_split = max(temp), by(st_code dt_code)
la var flag_91dist_split "Flag for 1991 district splits, requiring 2000 NSS splits"
unique st_code dt_code
local uniq = r(unique)
unique st_code dt_code if flag_91dist_split
di r(unique)/`uniq' // 35% of districts
drop temp

	// Populate flag for states with iffy 1991 disctrict matches
egen temp = max(flag_91_match_iffy), by(st_code dt_code)
replace flag_91_match_iffy = temp if flag_91_match_iffy==.
drop temp

	// Create cluster variable to acocunt for district splits post-1991
egen stdt = group(st_code dt_code)
egen temp1 = min(stdt), by(nss_hh_id)
egen temp2 = max(stdt), by(nss_hh_id) 
unique stdt
unique stdt if temp1<temp2 // 214 districts we need to make a bigger cluster for
preserve
keep stdt temp1 temp2
duplicates drop
drop if stdt==.
duplicates t stdt, gen(dup)
unique stdt if dup>0
drop if dup>0 & temp1==temp2
unique stdt
assert r(unique)==r(N)
gen stdt_cluster = stdt if dup==0
replace stdt_cluster = temp1 if dup==1
assert stdt_cluster!=.
unique stdt_cluster
keep stdt stdt_cluster
tempfile stdt_cluster
save `stdt_cluster'
restore
merge m:1 stdt using `stdt_cluster', nogen
la var stdt_cluster "Cluster variable that accounts for district splits post-1991"

	// Confirm weights still sum to 1
egen temp = sum(weight_normalized), by(st_code dt_code year)	
tab temp year if st_code!=. & dt_code!=.
drop temp

	// Clean up
drop st_codeNSS dt_codeNSS sum_wgt_combined dup* stdt temp*
drop if dt_code==.
unique st_code dt_code nss_hh_id
assert r(unique)==r(N)
la var nss_hh_id "NSS houshold id (not unique here, due to district splits)"

	// Align variable names
rename monthly_per_capita_exp_30 mth_pc_exp
rename *_yn *
rename electricity_* elec_*
rename implied_elec_price elec_price
rename sewing_machine sewing_mach
rename elec_q elec_q_yn
gen mth_pc_expE1 = mth_pc_exp - elec_value/household_size
gen mth_pc_expE2 = mth_pc_exp - 2*(elec_value/household_size)
la var mth_pc_expE1 "Monthly exp per capita less electricity spending"
la var mth_pc_expE2 "Monthly exp per capita less electricity spending (2x)"

	// Save
order st_code dt_code year
sort st_code dt_code year
compress
save "$nss/nss_hhlevel_uncollapsed.dta", replace
}

********************************************************************************
********************************************************************************

** Step 5: Construct RGGVY district-level panel, and merge with NSS panel (collapsed)
{
use "$panel/panel_dataset_dd.dta", clear
foreach v of varlist tot_p tot_p01 {
	egen double temp = sum(`v'), by(year st_code dt_code)
	replace `v' = temp
	drop temp
}
collapse (max) corr_state, by(year st_code dt_code state district tot_p tot_p01 /// 
	vplan4 vdpr4 stdt treat_x_post sample_1011) fast
unique st_code dt_code year
assert r(unique)==r(N)

replace year = 2010 if year==2011
replace year = 2000 if year==2001
expand 2 if year==2000, gen(temp)
replace year = 2005 if temp==1
drop temp
unique st_code dt_code year
assert r(unique)==r(N)

sort st_code dt_code year	
replace tot_p = . if year==2005
egen temp1 = mean(tot_p) if year==2000, by(st_code dt_code)
egen temp2 = mean(tot_p) if year==2010, by(st_code dt_code)
egen temp3 = mean(temp1), by(st_code dt_code)
egen temp4 = mean(temp2), by(st_code dt_code)
replace tot_p = (temp3+temp4)/2 if year==2005
drop temp*

merge 1:1 st_code dt_code year using "$nss/nss_hhlevel_collapsed.dta"
tab year _merge
tab year _merge if sample_1011==1
tab year _merge if corr_state==1
gen merge = _merge==3
egen stateyr = group(state year)

	// Drop states/UTs with zero districts that ever match
egen temp = mode(state), by(st_code)
replace state = temp if state==""
tab state _merge if year==2000 // no J&K in 2000
tab state _merge if year==2005
tab state _merge if year==2010 // 24 districts aren't represented in 2011
egen temp2 = max(merge), by(st_code)
tab st_code state if temp2==0, missing
	// Chandigarh, Dedechli, Daman & Diu, Dadra & Nagar Haveli, Goa, Lakshadweep, Puducherry, Andaman & Nicobar Islands
drop if temp2==0
drop temp*

correlate tot_p sum_wgts if year==2010
correlate tot_p sum_wgts if year==2005
correlate tot_p sum_wgts if year==2000
twoway scatter sum_wgts tot_p if year==2010
twoway scatter sum_wgts tot_p if year==2005
twoway scatter sum_wgts tot_p if year==2000

	// Number of NSS waves matched to district d
egen n_waves = sum(merge), by(st_code dt_code)
tab n_waves
la var n_waves "Number of NSS waves for district"

	// Diagnose non-matches
egen temp = max(n_waves==0), by(st_code)
order state district year st_code dt_code	
sort st_code dt_code year
br state district year st_code dt_code n_waves merge if temp==1
	// if we use data internal to NSS, these missings should be ok

	// Drop non-matched
drop if merge==0
drop merge _merge temp
	
	// Quartiles of 2005 expenditure (within state)
foreach p in 25 50 75 {
	egen temp`p' = pctile(mth_pc_exp) if year==2005, by(st_code) p(`p')
	egen temp`p'b = mean(temp`p'), by(st_code)
}
egen temp_2005 = mean(mth_pc_exp) if year==2005, by(st_code dt_code)
egen temp_2005b = mean(temp_2005), by(st_code dt_code)
gen exp05_st_4ile = .
replace exp05_st_4ile = 1 if temp_2005b<=temp25b
replace exp05_st_4ile = 2 if temp_2005b>temp25b & temp_2005b<=temp50b
replace exp05_st_4ile = 3 if temp_2005b>temp50b & temp_2005b<=temp75b
replace exp05_st_4ile = 4 if temp_2005b>temp75b 
tab st_code exp05_st_4ile
drop temp*
la var exp05_st_4ile "Within-state quartiles in 2005 expenditure/capita"

	// Quintiles of 2005 expenditure (within state)
foreach p in 20 40 60 80 {
	egen temp`p' = pctile(mth_pc_exp) if year==2005, by(st_code) p(`p')
	egen temp`p'b = mean(temp`p'), by(st_code)
}
egen temp_2005 = mean(mth_pc_exp) if year==2005, by(st_code dt_code)
egen temp_2005b = mean(temp_2005), by(st_code dt_code)
gen exp05_st_5ile = .
replace exp05_st_5ile = 1 if temp_2005b<=temp20b
replace exp05_st_5ile = 2 if temp_2005b>temp20b & temp_2005b<=temp40b
replace exp05_st_5ile = 3 if temp_2005b>temp40b & temp_2005b<=temp60b
replace exp05_st_5ile = 4 if temp_2005b>temp60b & temp_2005b<=temp80b
replace exp05_st_5ile = 5 if temp_2005b>temp80b 
tab st_code exp05_st_5ile
drop temp*
la var exp05_st_5ile "Within-state quintiles in 2005 expenditure/capita"

	// Deciles of 2005 expenditure (nationally)
foreach p in 10 20 30 40 50 60 70 80 90 {
	egen temp`p' = pctile(mth_pc_exp) if year==2005, p(`p')
	egen temp`p'b = mean(temp`p')
}
egen temp_2005 = mean(mth_pc_exp) if year==2005, by(st_code dt_code)
egen temp_2005b = mean(temp_2005), by(st_code dt_code)
gen exp05_ntl_10ile = .
replace exp05_ntl_10ile = 1 if temp_2005b<=temp10b
replace exp05_ntl_10ile = 2 if temp_2005b>temp10b & temp_2005b<=temp20b
replace exp05_ntl_10ile = 3 if temp_2005b>temp20b & temp_2005b<=temp30b
replace exp05_ntl_10ile = 4 if temp_2005b>temp30b & temp_2005b<=temp40b
replace exp05_ntl_10ile = 5 if temp_2005b>temp40b & temp_2005b<=temp50b
replace exp05_ntl_10ile = 6 if temp_2005b>temp50b & temp_2005b<=temp60b
replace exp05_ntl_10ile = 7 if temp_2005b>temp60b & temp_2005b<=temp70b
replace exp05_ntl_10ile = 8 if temp_2005b>temp70b & temp_2005b<=temp80b
replace exp05_ntl_10ile = 9 if temp_2005b>temp80b & temp_2005b<=temp90b
replace exp05_ntl_10ile = 10 if temp_2005b>temp90b 
tab state exp05_ntl_10ile if year==2005, missing
drop temp*
la var exp05_ntl_10ile "National deciles in 2005 expenditure/capita"

	// Pre-period DD dummy
gen treat_x_post05 = 0
replace treat_x_post05 = 1 if vplan4<11 & year>=2005
la var treat_x_post05 "DD indicator if treatment occurred before 2005"

	// Log-transform variables
gen log_exp_30 = log(mth_pc_exp)
assert log_exp_30!=.
gen log_exp_30E1 = log(mth_pc_expE1)
gen log_exp_30E2 = log(mth_pc_expE2)
la var log_exp_30 "Log of mth_pc_exp"
la var log_exp_30E1 "Log of mth_pc_expE1"
la var log_exp_30E2 "Log of mth_pc_expE2"
foreach v of varlist mth_pc_exp_* {
	local stub = subinstr("`v'","mth_pc_exp_","",.)
	gen log_exp_30_`stub' = log(`v')
	la var log_exp_30_`stub' "Log of `v'"
}
foreach v of varlist mth_pc_expE1_* {
	local stub = subinstr("`v'","mth_pc_expE1_","",.)
	gen log_exp_30E1_`stub' = log(`v')
	la var log_exp_30E1_`stub' "Log of `v'"
}
foreach v of varlist mth_pc_expE2_* {
	local stub = subinstr("`v'","mth_pc_expE2_","",.)
	gen log_exp_30E2_`stub' = log(`v')
	la var log_exp_30E2_`stub' "Log of `v'"
}

gen log_elec_q = log(elec_quantity)
gen ihs_elec_q = log(elec_quantity + sqrt(elec_quantity^2+1))
twoway scatter log_elec ihs_elec
la var log_elec_q "Log of elec_quantity"
la var ihs_elec_q "IHS of elec_quantity"
foreach v of varlist elec_quantity_* {
	local stub = subinstr("`v'","elec_quantity_","",.)
	gen log_elec_q_`stub' = log(`v')
	gen ihs_elec_q_`stub' = log(`v' + sqrt(`v'^2+1))
	la var log_elec_q_`stub' "Log of `v'"
	la var ihs_elec_q_`stub' "IHS of `v'"
}

	// Parse district FEs vs vDPR FEs
egen temp1 = min(stdt), by(vdpr4)
egen temp2 = max(stdt), by(vdpr4)
egen tag1 = tag(vdpr4) 
count if tag1 & temp1<temp2 & vdpr4!=. // 9 vDPRs have multiple districts
count if tag1 & temp1==temp2 & vdpr4!=. // 508 vDPRs have a single district

egen temp3 = min(vdpr4), by(stdt)
egen temp4 = max(vdpr4), by(stdt)
assert temp3==temp4 // all districts have at most 1 vDPR

	// Fixed effects at district level
	// Cluster at DPR-district level

	// Create approprate cluster variable, populating missing vDPRs with stdt
sum vdpr4, detail
sum stdt, detail
gen clustvar = vdpr4
replace clustvar = stdt+100000 if clustvar==.
assert clustvar!=.
egen temp5 = min(clustvar), by(vdpr4)
egen temp6 = max(clustvar), by(vdpr4)
assert temp5==temp6 if vdpr4!=.
egen temp7 = min(clustvar), by(stdt)
egen temp8 = max(clustvar), by(stdt)
assert temp7==temp8
drop temp* tag*
la var clustvar "Cluster variable = vDPR4, or stdt (where vDPR4 is missing)"

	// Pretrend in expenditure/capita, 2000 --> 2005
egen temp1 = mean(mth_pc_exp) if year==2000, by(st_code dt_code)
egen temp2 = mean(mth_pc_exp) if year==2005, by(st_code dt_code)
egen temp3 = mean(temp1), by(st_code dt_code)
egen temp4 = mean(temp2), by(st_code dt_code)
gen pretrend_exp30 = temp4-temp3
hist pretrend_exp30 if year==2010
drop temp*
la var pretrend_exp30 "2000-to-2005 delta in mth_pc_exp"

	// For heterogeneities: 2005 expenditure
egen temp_2005 = mean(mth_pc_exp) if year==2005, by(st_code dt_code)
egen exp_30_2005 = mean(temp_2005), by(st_code dt_code)
gen log_exp_30_2005 = log(exp_30_2005)
la var exp_30_2005 "2005 value of mth_pc_exp"
la var log_exp_30_2005 "Log of 2005 value of mth_pc_exp"
drop temp*

	// Compress and save
sort st_code dt_code year
unique st_code dt_code year
assert r(unique)==r(N)
compress
save "$panel/panel_dataset_dd_nss.dta", replace

}

********************************************************************************
********************************************************************************

** Step 6: Merge RGGVY variables into uncollapsed NSS panel
{
	// Keep relevant variables from district-yer panel
use "$panel/panel_dataset_dd_nss.dta", clear
keep state-corr_state stateyr-treat_x_post05 pretrend_exp30 exp_30_2005 log_exp_30_2005
rename pretrend_exp30 pretrend_exp30_dist
rename exp_30_2005 exp_30_2005_dist
rename log_exp_30_2005 log_exp_30_2005_dist
la var pretrend_exp30_dist "2000-to-2005 district-wide avg delta in mth_pc_exp"
la var exp_30_2005 "2005 district-wide avg mth_pc_exp"
la var log_exp_30_2005 "Log of 2005 district-wide avg mth_pc_exp"
	
	// Merge in uncollapsed NSS panel
merge 1:m st_code dt_code year using "$nss/nss_hhlevel_uncollapsed.dta"
order stateyr-treat_x_post05 pretrend_exp30 exp_30_2005 log_exp_30_2005, last
drop if _merge==2
drop _merge
	
	// Log-transform variables
gen log_exp_30 = log(mth_pc_exp)
gen log_exp_30E1 = log(mth_pc_expE1)
gen log_exp_30E2 = log(mth_pc_expE2)
la var log_exp_30 "Log of mth_pc_exp"
la var log_exp_30E1 "Log of mth_pc_expE1"
la var log_exp_30E2 "Log of mth_pc_expE2"
gen log_elec_q = log(elec_quantity)
gen ihs_elec_q = log(elec_quantity + sqrt(elec_quantity^2+1))
twoway scatter log_elec ihs_elec
la var log_elec_q "Log of elec_quantity"
la var ihs_elec_q "IHS of elec_quantity"

	// Parse district FEs vs vDPR FEs
egen temp1 = min(stdt_cluster), by(vdpr4)
egen temp2 = max(stdt_cluster), by(vdpr4)
egen tag1 = tag(vdpr4) 
count if tag1 & temp1<temp2 & vdpr4!=. // 7 vDPRs have multiple (unsplit) districts
count if tag1 & temp1==temp2 & vdpr4!=. // 510 vDPRs have a single (unsplit) district

egen temp3 = min(vdpr4), by(stdt_cluster)
egen temp4 = max(vdpr4), by(stdt_cluster)
count if temp3<temp4 // some (unsplit) districts have at more than 1 vDPR

	// Fixed effects at district level
	// Cluster at larger of {DPR, (unsplit) district} level

	// Create approprate cluster variable, populating missing vDPRs with stdt
preserve 
keep stdt_cluster vdpr4 temp?
duplicates drop 
	// start with unique 1-to-1 (unsplit) districts and vDPR
gen stdt_cluster_new = stdt_cluster if temp1==temp2 & temp3==temp4
	// for multiple vDPRs witihn (unsplit) district, stick with unsplit district
replace stdt_cluster_new = stdt_cluster if stdt_cluster_new==. & temp1==temp2
	// for multiple (unsplit) districts within a vDPR, use smaller indexed (unsplit) district
replace stdt_cluster_new = temp1 if stdt_cluster_new==. & vdpr4!=. & temp1<temp2	
	// for missing vDPRs, use (unsplit) district
replace stdt_cluster_new = stdt_cluster if stdt_cluster_new==. & vdpr4==.	
assert stdt_cluster_new!=.
	// Confirm that everything is appropriately grouped
egen temp5 = min(stdt_cluster_new), by(vdpr4)
egen temp6 = max(stdt_cluster_new), by(vdpr4)
egen temp7 = min(stdt_cluster_new), by(stdt_cluster)
egen temp8 = max(stdt_cluster_new), by(stdt_cluster)	
assert temp5==temp6 if vdpr4!=.
br if temp7<temp8
replace stdt_cluster_new = temp7 if temp7<temp8
egen temp9 = min(stdt_cluster_new), by(stdt_cluster)
egen temp10 = max(stdt_cluster_new), by(stdt_cluster)	
assert temp9==temp10	
egen temp11 = min(stdt_cluster_new), by(vdpr4)
egen temp12 = max(stdt_cluster_new), by(vdpr4)
assert temp11==temp12 if vdpr4!=.
unique stdt_cluster_new
keep vdpr4 stdt_cluster stdt_cluster_new
tempfile stdt_cluster
save `stdt_cluster'
restore
merge m:1 vdpr4 stdt_cluster using `stdt_cluster', nogen
rename stdt_cluster stdt_presplit 
la var stdt_presplit "District group that accounts for district splits post-1991"
rename stdt_cluster_new stdt_cluster
la var stdt_cluster "Cluster variable accounting for dist splits post-1991 AND non-1-to-1-DPRs"
drop temp* tag*
	
	// Compress and save
sort st_code dt_code year
compress
save "$panel/panel_dataset_dd_nss_uncollapsed.dta", replace
	
}	
	   
********************************************************************************
********************************************************************************

