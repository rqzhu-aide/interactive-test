clear all
set more off
set mem 10000000
set matsize 10000

*****************************************************************************************
*** ALL NSS REGRESSIONS (first stage, reduced form, IV, sensitivities, split samples) ***
*****************************************************************************************

** Set file paths
do "$path_code/paths.do"

** Set graph scheme
cd "$path/code/analyze"
set scheme fb, perm

********************************************************************************
********************************************************************************

** 1. Collapsed regressions, non-IV
{
use "$panel/panel_dataset_dd_nss.dta", clear
set obs 100000

global yvars = "elec_quantity log_elec_q elec_q_yn mth_pc_exp log_exp_30 mth_pc_expE1 log_exp_30E1 mth_pc_expE2 log_exp_30E2 " ///
				+ "elec_light tv fan ac fridge othfuel_val"
global ytags = "none dec12 dec30 under500 over500 under1k over1k under2k over2k under4k over4k " 
			 
global ddvar = "treat_x_post"
global ivvar = ""
global vce = "cluster clustvar"

gen panel = "district-year collapsed"
gen regs = "ols"
gen yvar = ""
gen ytag = ""
gen ddvar = ""
gen ivvar = ""
gen fes = ""
gen ifs = ""
gen vce = ""
gen beta = .
gen se = .
gen tscore = .
gen pvalue = .
gen ci95_lo = .
gen ci95_hi = .
gen ymean_pooled = .
gen ymean_2000 = .
gen ymean_2005 = .
gen ymean_2010_ctrl = .
gen nobs = .
gen nclust = .
gen r2 = .
gen fstat = .
gen rmse = .
gen row_id = .
local row_id = 1

foreach yvar in $yvars {
		
	foreach ytags in $ytags {
		
		if "`ytags'"=="none" {
			local ytag = ""
		}
		else {
			local ytag = "_`ytags'"
		}

		forvalues fes = 1/6 {
			
			if `fes'==1 {
				local fe = "year stdt"
			}
			else if `fes'==2 {
				local fe = "year c.year#st_code stdt"
			}
			else if `fes'==3 {
				local fe = "year c.year#exp05_st_4ile stdt"
			}
			else if `fes'==4 {
				local fe = "year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt"
			}
			else if `fes'==5 {
				local fe = "year c.year#exp05_st_4ile c.year#st_code stdt"
			}
			else if `fes'==6 {
				local fe = "year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt"
			}
			
			forvalues ifs = 1/5 {
			
				if `ifs'==1 {
					local if = ""
				}
				else if `ifs'==2 {
					local if = " if year>2000"
				}
				else if `ifs'==3 {
					local if = " if sample_1011"
				}
				else if `ifs'==4 {
					local if = " if flag_91_match_iffy==0"
				}
				else if `ifs'==5 {
					local if = " if flag_91dist_split==0"
				}
		
				if !(("`if'"==" if year>2000") & (regexm("`ytag'","k") | substr("`tag'",-3,3)=="500")) {
					
					local ddvar = "$ddvar"
					local ivvar = "$ivvar"
					local vce = "$vce"
					
					reghdfe `yvar'`ytag' `ddvar' `if' , a(`fe') vce(`vce')

					replace yvar = "`yvar'" in `row_id'
					replace ytag = "`ytag'" in `row_id'
					replace ddvar = "`ddvar'" in `row_id'
					replace ivvar = subinstr("`ivvar'",".","",1) in `row_id'
					replace fes = "`fe'" in `row_id'
					replace ifs = "`if'" in `row_id'
					replace vce = "`vce'" in `row_id'
					replace beta = _b[`ddvar'] in `row_id'
					replace se = _se[`ddvar'] in `row_id'
					replace tscore = _b[`ddvar']/_se[`ddvar'] in `row_id'
					replace pvalue = 2*ttail(e(df_r),abs(_b[`ddvar']/_se[`ddvar'])) in `row_id'
					replace ci95_lo = _b[`ddvar'] - _se[`ddvar']*invttail(e(df_r),0.025) in `row_id'
					replace ci95_hi = _b[`ddvar'] + _se[`ddvar']*invttail(e(df_r),0.025) in `row_id'
					sum `yvar'`ytag' if e(sample)
					replace ymean_pooled = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & year==2000
					replace ymean_2000 = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & year==2005
					replace ymean_2005 = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & year==2010 & `ddvar'==0
					replace ymean_2010_ctrl = r(mean) in `row_id'
					replace nobs = e(N) in `row_id'
					replace nclust =  e(N_clust) in `row_id'
					replace r2 = e(r2) in `row_id'
					replace fstat = e(rkf) in `row_id'
					replace rmse = e(rmse) in `row_id'
					replace row_id = `row_id' in `row_id'
					local row_id = `row_id'+1
				}	
			}
		}
	}
}

keep panel-row_id
drop if _n>=`row_id'
compress
save "$results/nss_reg_results.dta", replace

}

********************************************************************************
********************************************************************************

** 2. Collapsed regressions, IV
{
use "$panel/panel_dataset_dd_nss.dta", clear
set obs 100000

global yvars = "mth_pc_exp log_exp_30 mth_pc_expE1 log_exp_30E1 mth_pc_expE2 log_exp_30E2 tv"
global ytags = "none dec12 dec30 under500 over500 under1k over1k under2k over2k under4k over4k " 

global ddvar = "elec_q_yn"
global ivvar = "treat_x_post"
global vce = "cluster clustvar"
if "$ivvar"!="" {
	global vce = subinstr("$vce","cluster ","",1)
}

gen panel = "district-year collapsed"
gen regs = "iv"
gen yvar = ""
gen ytag = ""
gen ddvar = ""
gen ivvar = ""
gen fes = ""
gen ifs = ""
gen vce = ""
gen beta = .
gen se = .
gen tscore = .
gen pvalue = .
gen ci95_lo = .
gen ci95_hi = .
gen ymean_pooled = .
gen ymean_2000 = .
gen ymean_2005 = .
gen ymean_2010_ctrl = .
gen nobs = .
gen nclust = .
gen r2 = .
gen fstat = .
gen rmse = .
gen row_id = .
local row_id = 1

foreach yvar in $yvars {
		
	foreach ytags in $ytags {
		
		if "`ytags'"=="none" {
			local ytag = ""
		}
		else {
			local ytag = "_`ytags'"
		}

		forvalues fes = 1/6 {
			
			if `fes'==1 {
				local fe = "year stdt"
			}
			else if `fes'==2 {
				local fe = "year c.year#st_code stdt"
			}
			else if `fes'==3 {
				local fe = "year c.year#exp05_st_4ile stdt"
			}
			else if `fes'==4 {
				local fe = "year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt"
			}
			else if `fes'==5 {
				local fe = "year c.year#exp05_st_4ile c.year#st_code stdt"
			}
			else if `fes'==6 {
				local fe = "year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt"
			}
			
			forvalues ifs = 1/5 {
			
				if `ifs'==1 {
					local if = ""
				}
				else if `ifs'==2 {
					local if = " if year>2000"
				}
				else if `ifs'==3 {
					local if = " if sample_1011"
				}
				else if `ifs'==4 {
					local if = " if flag_91_match_iffy==0"
				}
				else if `ifs'==5 {
					local if = " if flag_91dist_split==0"
				}
		
				if !(("`if'"==" if year>2000") & (regexm("`ytag'","k") | substr("`tag'",-3,3)=="500")) {

					local ddvar = "$ddvar`ytag'"
					local ivvar = "$ivvar"
					local vce = "$vce"
					
					ivreghdfe `yvar'`ytag' (`ddvar' = `ivvar') `if' , a(`fe') cluster(`vce')

					replace yvar = "`yvar'" in `row_id'
					replace ytag = "`ytag'" in `row_id'
					replace ddvar = "`ddvar'" in `row_id'
					replace ivvar = subinstr("`ivvar'",".","",1) in `row_id'
					replace fes = "`fe'" in `row_id'
					replace ifs = "`if'" in `row_id'
					replace vce = "`vce'" in `row_id'
					replace beta = _b[`ddvar'] in `row_id'
					replace se = _se[`ddvar'] in `row_id'
					replace tscore = _b[`ddvar']/_se[`ddvar'] in `row_id'
					replace pvalue = 2*ttail(e(df_r),abs(_b[`ddvar']/_se[`ddvar'])) in `row_id'
					replace ci95_lo = _b[`ddvar'] - _se[`ddvar']*invttail(e(df_r),0.025) in `row_id'
					replace ci95_hi = _b[`ddvar'] + _se[`ddvar']*invttail(e(df_r),0.025) in `row_id'
					sum `yvar'`ytag' if e(sample)
					replace ymean_pooled = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & year==2000
					replace ymean_2000 = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & year==2005
					replace ymean_2005 = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & year==2010 & `ivvar'==0
					replace ymean_2010_ctrl = r(mean) in `row_id'
					replace nobs = e(N) in `row_id'
					replace nclust =  e(N_clust) in `row_id'
					replace r2 = e(r2) in `row_id'
					replace fstat = e(rkf) in `row_id'
					replace rmse = e(rmse) in `row_id'
					replace row_id = `row_id' in `row_id'
					local row_id = `row_id'+1
					
				}
			}
		}
	}
}

keep panel-row_id
drop if _n>=`row_id'
tempfile newregs
save `newregs'
append using "$results/nss_reg_results.dta" `newregs'
duplicates drop
compress 
save "$results/nss_reg_results.dta", replace

}

********************************************************************************
********************************************************************************

** 3. Collapsed regressions, non-IV, pretrends
{
use "$panel/panel_dataset_dd_nss.dta", clear
set obs 100000

global yvars = "elec_quantity log_elec_q elec_q_yn mth_pc_exp log_exp_30 mth_pc_expE1 log_exp_30E1 mth_pc_expE2 log_exp_30E2 " ///
				+ "elec_light tv fan ac fridge othfuel_val"
global ytags = "none dec12 dec30"

global ddvar = "treat_x_post05"
global ivvar = ""
global vce = "cluster clustvar"

gen panel = "district-year collapsed"
gen regs = "ols (pretrends)"
gen yvar = ""
gen ytag = ""
gen ddvar = ""
gen ivvar = ""
gen fes = ""
gen ifs = ""
gen vce = ""
gen beta = .
gen se = .
gen tscore = .
gen pvalue = .
gen ci95_lo = .
gen ci95_hi = .
gen ymean_pooled = .
gen ymean_2000 = .
gen ymean_2005 = .
gen ymean_2010_ctrl = .
gen nobs = .
gen nclust = .
gen r2 = .
gen fstat = .
gen rmse = .
gen row_id = .
local row_id = 1

foreach yvar in $yvars {
		
	foreach ytags in $ytags {
		
		if "`ytags'"=="none" {
			local ytag = ""
		}
		else {
			local ytag = "_`ytags'"
		}

		forvalues fes = 1/6 {
			
			if `fes'==1 {
				local fe = "year stdt"
			}
			else if `fes'==2 {
				local fe = "year c.year#st_code stdt"
			}
			else if `fes'==3 {
				local fe = "year c.year#exp05_st_4ile stdt"
			}
			else if `fes'==4 {
				local fe = "year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt"
			}
			else if `fes'==5 {
				local fe = "year c.year#exp05_st_4ile c.year#st_code stdt"
			}
			else if `fes'==6 {
				local fe = "year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt"
			}
			
			forvalues ifs = 1/4 {
			
				if `ifs'==1 {
					local if = " if year<2010"
				}
				else if `ifs'==2 {
					local if = " if year<2010 & sample_1011"
				}
				else if `ifs'==3 {
					local if = " if year<2010 & flag_91_match_iffy==0"
				}
				else if `ifs'==4 {
					local if = " if year<2010 & flag_91dist_split==0"
				}
		
				if !(regexm("`ytag'","k") | substr("`tag'",-3,3)=="500") {
		
					local ddvar = "$ddvar"
					local ivvar = "$ivvar"
					local vce = "$vce"
					
					reghdfe `yvar'`ytag' `ddvar' `if' , a(`fe') vce(`vce')

					replace yvar = "`yvar'" in `row_id'
					replace ytag = "`ytag'" in `row_id'
					replace ddvar = "`ddvar'" in `row_id'
					replace ivvar = subinstr("`ivvar'",".","",1) in `row_id'
					replace fes = "`fe'" in `row_id'
					replace ifs = "`if'" in `row_id'
					replace vce = "`vce'" in `row_id'
					replace beta = _b[`ddvar'] in `row_id'
					replace se = _se[`ddvar'] in `row_id'
					replace tscore = _b[`ddvar']/_se[`ddvar'] in `row_id'
					replace pvalue = 2*ttail(e(df_r),abs(_b[`ddvar']/_se[`ddvar'])) in `row_id'
					replace ci95_lo = _b[`ddvar'] - _se[`ddvar']*invttail(e(df_r),0.025) in `row_id'
					replace ci95_hi = _b[`ddvar'] + _se[`ddvar']*invttail(e(df_r),0.025) in `row_id'
					sum `yvar'`ytag' if e(sample)
					replace ymean_pooled = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & year==2000
					replace ymean_2000 = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & year==2005
					replace ymean_2005 = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & year==2010 & `ddvar'==0
					replace ymean_2010_ctrl = r(mean) in `row_id'
					replace nobs = e(N) in `row_id'
					replace nclust =  e(N_clust) in `row_id'
					replace r2 = e(r2) in `row_id'
					replace fstat = e(rkf) in `row_id'
					replace rmse = e(rmse) in `row_id'
					replace row_id = `row_id' in `row_id'
					local row_id = `row_id'+1
				}	
			}
		}
	}
}

keep panel-row_id
drop if _n>=`row_id'
tempfile newregs
save `newregs'
append using "$results/nss_reg_results.dta" `newregs'
duplicates drop
compress 
save "$results/nss_reg_results.dta", replace


}

********************************************************************************
********************************************************************************

** 4. Collapsed regressions, non-IV, RGGVY intensity (interacted)
{
use "$panel/panel_dataset_full.dta", clear

	// Bring in RGGVY district-level administrative data (10th Plan only)
preserve
use "$rggvy/rggvy_district_progress_X_XI_processed.dta", clear
egen dt_group = group(st_code dt_code)
egen temp_group = group(plan implement_type)
unique st_code, by(temp_group) gen(uniq_st)
unique dt_group, by(temp_group) gen(uniq_dt)
unique dpr_code, by(temp_group) gen(uniq_dpr)
unique st_code if plan==10
unique st_code if plan==11
unique dt_group if plan==10
unique dt_group if plan==11
count if award_date<sanction_date
replace award_date = sanction_date if award_date<sanction_date
replace award_date = max(award_date,17553) if plan==11
keep if plan==10
collapse (min) min_award_date=award_date (max) max_award_date=award_date ///
	(sum) award_cost total_released achiev_UDE achiev_ELEC achiev_BPL ///
	, by(st_code dt_code)	
gen med_award_date = round((min_award_date+max_award_date)/2,1)
format %td med_award_date	
tempfile admin
save `admin'
restore	
merge m:1 st_code dt_code using `admin' 

	// RGGVY admin splitter 1: (# villages treated) / (# villages in district)
egen temp1 = count(vi_code) if tot_p>=300, by(st_code dt_code)
egen temp2 = mode(temp1), by(st_code dt_code)
gen RGGVY_share_villages_300 = (achiev_UDE + achiev_ELEC) / temp2
egen temp3 = count(vi_code), by(st_code dt_code)
gen RGGVY_share_villages_all = (achiev_UDE + achiev_ELEC) / temp3
egen temp_tag = tag(st_code dt_code) 
twoway scatter RGGVY_share_villages_300 RGGVY_share_villages_all if temp_tag
tab state if temp_tag & RGGVY_share_villages_300>1.4 & RGGVY_share_villages_all!=. & corr_state==1
gen RGGVY_rule_breaker = RGGVY_share_villages_300>1.4
twoway scatter RGGVY_share_villages_300 RGGVY_share_villages_all if temp_tag & RGGVY_rule_breaker==0
sum RGGVY_share_villages_all if temp_tag & RGGVY_rule_breaker==0, detail
sum RGGVY_share_villages_300 if temp_tag & RGGVY_rule_breaker==0, detail
// split on 60% of villages in district
drop temp*

	// RGGVY admin splitter 2: (# BPL HHs treated) / (# village HHs in district)
egen temp1 = sum(no_hh11) if tot_p>=300, by(st_code dt_code)
egen temp2 = mode(temp1), by(st_code dt_code)
gen RGGVY_share_hh_300 = (achiev_BPL) / temp2
egen temp3 = sum(no_hh11), by(st_code dt_code)
gen RGGVY_share_hh_all = (achiev_BPL) / temp3
egen temp_tag = tag(st_code dt_code) 
twoway scatter RGGVY_share_hh_300 RGGVY_share_hh_all if temp_tag 
twoway scatter RGGVY_share_hh_300 RGGVY_share_hh_all if temp_tag & RGGVY_rule_breaker==0
sum RGGVY_share_hh_all if temp_tag & RGGVY_rule_breaker==0, detail
sum RGGVY_share_hh_300 if temp_tag & RGGVY_rule_breaker==0, detail
// split on 10% of HHs in district
drop temp*

	// RGGVY admin splitter 3: (Rs allocated) / (# villages treated)
egen temp_tag = tag(st_code dt_code) 
gen RGGVY_lakh_per_v = (total_released) /  (achiev_UDE + achiev_ELEC)
sum RGGVY_lakh_per_v if temp_tag & RGGVY_rule_breaker==0, detail
// split on 10 lakh per village
drop temp*

keep st_code dt_code RGGVY_rule_breaker RGGVY_share_villages_all RGGVY_share_hh_all RGGVY_lakh_per_v
duplicates drop
merge 1:m st_code dt_code using "$panel/panel_dataset_dd_nss.dta"

gen DPR = 0
replace DPR = 1 if (RGGVY_rule_breaker==0) & (RGGVY_share_villages_all>=0.60)
replace DPR = . if RGGVY_rule_breaker==1 & vplan4<11


set obs 10000

global yvars = "elec_quantity log_elec_q elec_q_yn mth_pc_exp log_exp_30 mth_pc_expE1 log_exp_30E1 mth_pc_expE2 log_exp_30E2 " ///
				+ "elec_light tv fan ac fridge"
global ytags = "none dec12 dec30" 

global ddvar_dpr_hi = "1.DPR#c.treat_x_post"
global ddvar_dpr_lo = "0.DPR#c.treat_x_post"
global ivvar = ""
global vce = "cluster clustvar"

gen panel = "district-year collapsed"
gen regs = "ols (DPR interaction)"
gen yvar = ""
gen ytag = ""
gen ddvar = ""
gen ivvar = ""
gen fes = ""
gen ifs = ""
gen vce = ""
gen beta_dpr_hi = .
gen se_dpr_hi = .
gen tscore_dpr_hi = .
gen pvalue_dpr_hi = .
gen ci95_lo_dpr_hi = .
gen ci95_hi_dpr_hi = .
gen beta_dpr_lo = .
gen se_dpr_lo = .
gen tscore_dpr_lo = .
gen pvalue_dpr_lo = .
gen ci95_lo_dpr_lo = .
gen ci95_hi_dpr_lo = .
gen pval_equal = .
gen ymean_pooled = .
gen ymean_2000 = .
gen ymean_2005 = .
gen ymean_dpr_hi = .
gen ymean_dpr_lo = .
gen nobs = .
gen nclust = .
gen r2 = .
gen fstat = .
gen rmse = .
gen row_id = .
local row_id = 1


foreach yvar in $yvars {
		
	foreach ytags in $ytags {
		
		if "`ytags'"=="none" {
			local ytag = ""
		}
		else {
			local ytag = "_`ytags'"
		}

		foreach fes in 1 2 {
			
			if `fes'==1 {
				local fe = "year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt"
			}
			else if `fes'==2 {
				local fe = "year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt"
			}
			
			foreach ifs in 1 {
			
				if `ifs'==1 {
					local if = ""
				}
		
				if !(("`if'"==" if year>2000") & (regexm("`ytag'","k") | substr("`tag'",-3,3)=="500")) {
					
					local ddvar_dpr_hi = "$ddvar_dpr_hi"
					local ddvar_dpr_lo = "$ddvar_dpr_lo"
					local ivvar = "$ivvar"
					local vce = "$vce"
					
					reghdfe `yvar'`ytag' `ddvar_dpr_hi' `ddvar_dpr_lo' `if' , a(`fe') vce(`vce')
					
					replace yvar = "`yvar'" in `row_id'
					replace ytag = "`ytag'" in `row_id'
					replace ddvar = "`ddvar'" in `row_id'
					replace ivvar = subinstr("`ivvar'",".","",1) in `row_id'
					replace fes = "`fe'" in `row_id'
					replace ifs = "`if'" in `row_id'
					replace vce = "`vce'" in `row_id'
					replace beta_dpr_hi = _b[`ddvar_dpr_hi'] in `row_id'
					replace se_dpr_hi = _se[`ddvar_dpr_hi'] in `row_id'
					replace tscore_dpr_hi = _b[`ddvar_dpr_hi']/_se[`ddvar_dpr_hi'] in `row_id'
					replace pvalue_dpr_hi = 2*ttail(e(df_r),abs(_b[`ddvar_dpr_hi']/_se[`ddvar_dpr_hi'])) in `row_id'
					replace ci95_lo_dpr_hi = _b[`ddvar_dpr_hi'] - _se[`ddvar_dpr_hi']*invttail(e(df_r),0.025) in `row_id'
					replace ci95_hi_dpr_hi = _b[`ddvar_dpr_hi'] + _se[`ddvar_dpr_hi']*invttail(e(df_r),0.025) in `row_id'
					replace beta_dpr_lo = _b[`ddvar_dpr_lo'] in `row_id'
					replace se_dpr_lo = _se[`ddvar_dpr_lo'] in `row_id'
					replace tscore_dpr_lo = _b[`ddvar_dpr_lo']/_se[`ddvar_dpr_lo'] in `row_id'
					replace pvalue_dpr_lo = 2*ttail(e(df_r),abs(_b[`ddvar_dpr_lo']/_se[`ddvar_dpr_lo'])) in `row_id'
					replace ci95_lo_dpr_lo = _b[`ddvar_dpr_lo'] - _se[`ddvar_dpr_lo']*invttail(e(df_r),0.025) in `row_id'
					replace ci95_hi_dpr_lo = _b[`ddvar_dpr_lo'] + _se[`ddvar_dpr_lo']*invttail(e(df_r),0.025) in `row_id'
					test `ddvar_dpr_hi'=`ddvar_dpr_lo'
					replace pval_equal = r(p) in `row_id'
					sum `yvar'`ytag' if e(sample)
					replace ymean_pooled = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & year==2000
					replace ymean_2000 = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & year==2005
					replace ymean_2005 = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & DPR==1
					replace ymean_dpr_hi = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & DPR==0
					replace ymean_dpr_lo = r(mean) in `row_id'
					replace nobs = e(N) in `row_id'
					replace nclust =  e(N_clust) in `row_id'
					replace r2 = e(r2) in `row_id'
					replace fstat = e(rkf) in `row_id'
					replace rmse = e(rmse) in `row_id'
					replace row_id = `row_id' in `row_id'
					local row_id = `row_id'+1
				}	
			}
		}
	}
}

keep panel-row_id
drop if _n>=`row_id'
tempfile newregs
save `newregs'
append using "$results/nss_reg_results.dta" `newregs'
duplicates drop
compress 
save "$results/nss_reg_results.dta", replace


}

********************************************************************************
********************************************************************************

** 5. Collapsed regressions, IV, RGGVY intensity (split)
{
use "$panel/panel_dataset_full.dta", clear

	// Bring in RGGVY district-level administrative data (10th Plan only)
preserve
use "$rggvy/rggvy_district_progress_X_XI_processed.dta", clear
egen dt_group = group(st_code dt_code)
egen temp_group = group(plan implement_type)
unique st_code, by(temp_group) gen(uniq_st)
unique dt_group, by(temp_group) gen(uniq_dt)
unique dpr_code, by(temp_group) gen(uniq_dpr)
unique st_code if plan==10
unique st_code if plan==11
unique dt_group if plan==10
unique dt_group if plan==11
count if award_date<sanction_date
replace award_date = sanction_date if award_date<sanction_date
replace award_date = max(award_date,17553) if plan==11
keep if plan==10
collapse (min) min_award_date=award_date (max) max_award_date=award_date ///
	(sum) award_cost total_released achiev_UDE achiev_ELEC achiev_BPL ///
	, by(st_code dt_code)	
gen med_award_date = round((min_award_date+max_award_date)/2,1)
format %td med_award_date	
tempfile admin
save `admin'
restore	
merge m:1 st_code dt_code using `admin' 

	// RGGVY admin splitter 1: (# villages treated) / (# villages in district)
egen temp1 = count(vi_code) if tot_p>=300, by(st_code dt_code)
egen temp2 = mode(temp1), by(st_code dt_code)
gen RGGVY_share_villages_300 = (achiev_UDE + achiev_ELEC) / temp2
egen temp3 = count(vi_code), by(st_code dt_code)
gen RGGVY_share_villages_all = (achiev_UDE + achiev_ELEC) / temp3
egen temp_tag = tag(st_code dt_code) 
twoway scatter RGGVY_share_villages_300 RGGVY_share_villages_all if temp_tag
tab state if temp_tag & RGGVY_share_villages_300>1.4 & RGGVY_share_villages_all!=. & corr_state==1
gen RGGVY_rule_breaker = RGGVY_share_villages_300>1.4
twoway scatter RGGVY_share_villages_300 RGGVY_share_villages_all if temp_tag & RGGVY_rule_breaker==0
sum RGGVY_share_villages_all if temp_tag & RGGVY_rule_breaker==0, detail
sum RGGVY_share_villages_300 if temp_tag & RGGVY_rule_breaker==0, detail
// split on 60% of villages in district
drop temp*

	// RGGVY admin splitter 2: (# BPL HHs treated) / (# village HHs in district)
egen temp1 = sum(no_hh11) if tot_p>=300, by(st_code dt_code)
egen temp2 = mode(temp1), by(st_code dt_code)
gen RGGVY_share_hh_300 = (achiev_BPL) / temp2
egen temp3 = sum(no_hh11), by(st_code dt_code)
gen RGGVY_share_hh_all = (achiev_BPL) / temp3
egen temp_tag = tag(st_code dt_code) 
twoway scatter RGGVY_share_hh_300 RGGVY_share_hh_all if temp_tag 
twoway scatter RGGVY_share_hh_300 RGGVY_share_hh_all if temp_tag & RGGVY_rule_breaker==0
sum RGGVY_share_hh_all if temp_tag & RGGVY_rule_breaker==0, detail
sum RGGVY_share_hh_300 if temp_tag & RGGVY_rule_breaker==0, detail
// split on 10% of HHs in district
drop temp*

	// RGGVY admin splitter 3: (Rs allocated) / (# villages treated)
egen temp_tag = tag(st_code dt_code) 
gen RGGVY_lakh_per_v = (total_released) /  (achiev_UDE + achiev_ELEC)
sum RGGVY_lakh_per_v if temp_tag & RGGVY_rule_breaker==0, detail
// split on 10 lakh per village
drop temp*

keep st_code dt_code RGGVY_rule_breaker RGGVY_share_villages_all RGGVY_share_hh_all RGGVY_lakh_per_v
duplicates drop
merge 1:m st_code dt_code using "$panel/panel_dataset_dd_nss.dta"

gen DPR = 0
replace DPR = 1 if (RGGVY_rule_breaker==0) & (RGGVY_share_villages_all>=0.60)
replace DPR = . if RGGVY_rule_breaker==1 & vplan4<11

set obs 10000

global yvars = "mth_pc_exp log_exp_30 mth_pc_expE1 log_exp_30E1 mth_pc_expE2 log_exp_30E2 tv " 
global ytags = "none dec12 dec30" 

global ddvar = "elec_q_yn"
global ivvar = "treat_x_post"
global vce = "cluster clustvar"
if "$ivvar"!="" {
	global vce = subinstr("$vce","cluster ","",1)
}

gen panel = "district-year collapsed"
gen regs = "iv (DPR split)"
gen yvar = ""
gen ytag = ""
gen ddvar = ""
gen ivvar = ""
gen fes = ""
gen ifs = ""
gen vce = ""
gen beta = .
gen se = .
gen tscore = .
gen pvalue = .
gen ci95_lo = .
gen ci95_hi = .
gen ymean_pooled = .
gen ymean_2000 = .
gen ymean_2005 = .
gen ymean_2010_ctrl = .
gen nobs = .
gen nclust = .
gen r2 = .
gen fstat = .
gen rmse = .
gen row_id = .
local row_id = 1


foreach yvar in $yvars {
		
	foreach ytags in $ytags {
		
		if "`ytags'"=="none" {
			local ytag = ""
		}
		else {
			local ytag = "_`ytags'"
		}

		foreach fes in 1 {
			
			if `fes'==1 {
				local fe = "year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt"
			}
			
			foreach ifs in 1 {
			
				if `ifs'==1 {
					local if = " if vplan4>=11 | DPR==1"
				}

				if !(("`if'"==" if year>2000") & (regexm("`ytag'","k") | substr("`tag'",-3,3)=="500")) {
					
					local ddvar = "$ddvar`ytag'"
					local ivvar = "$ivvar"
					local vce = "$vce"
					
					ivreghdfe `yvar'`ytag' (`ddvar' = `ivvar') `if' , a(`fe') cluster(`vce')

					replace yvar = "`yvar'" in `row_id'
					replace ytag = "`ytag'" in `row_id'
					replace ddvar = "`ddvar'" in `row_id'
					replace ivvar = subinstr("`ivvar'",".","",1) in `row_id'
					replace fes = "`fe'" in `row_id'
					replace ifs = "`if'" in `row_id'
					replace vce = "`vce'" in `row_id'
					replace beta = _b[`ddvar'] in `row_id'
					replace se = _se[`ddvar'] in `row_id'
					replace tscore = _b[`ddvar']/_se[`ddvar'] in `row_id'
					replace pvalue = 2*ttail(e(df_r),abs(_b[`ddvar']/_se[`ddvar'])) in `row_id'
					replace ci95_lo = _b[`ddvar'] - _se[`ddvar']*invttail(e(df_r),0.025) in `row_id'
					replace ci95_hi = _b[`ddvar'] + _se[`ddvar']*invttail(e(df_r),0.025) in `row_id'
					sum `yvar'`ytag' if e(sample)
					replace ymean_pooled = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & year==2000
					replace ymean_2000 = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & year==2005
					replace ymean_2005 = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & year==2010 & `ivvar'==0
					replace ymean_2010_ctrl = r(mean) in `row_id'
					replace nobs = e(N) in `row_id'
					replace nclust =  e(N_clust) in `row_id'
					replace r2 = e(r2) in `row_id'
					replace fstat = e(rkf) in `row_id'
					replace rmse = e(rmse) in `row_id'
					replace row_id = `row_id' in `row_id'
					local row_id = `row_id'+1
					
				}	
			}
		}
	}
}

keep panel-row_id
drop if _n>=`row_id'
tempfile newregs
save `newregs'
append using "$results/nss_reg_results.dta" `newregs'
duplicates drop
compress 
save "$results/nss_reg_results.dta", replace


}

********************************************************************************
********************************************************************************

** 6. Collapsed regressions, non-IV, Hours of power (interacted)
{
use "$panel/panel_dataset_full.dta", clear

	// Summarize hours of power to electrified villages, by district
egen temp1 = mean(vdp_pwr_h_all_avg) if vdp_pwr_h_all_avg_11>0, by(st_code dt_code)
egen HRS_all_wide = mode(temp1), by(st_code dt_code)
egen temp2 = mean(vdp_pwr_h_dom_avg) if vdp_pwr_h_dom_avg_11>0, by(st_code dt_code)
egen HRS_dom_wide = mode(temp2), by(st_code dt_code)
twoway scatter HRS_all_wide HRS_dom_wide

keep st_code dt_code HRS_all_wide HRS_dom_wide
duplicates drop
merge 1:m st_code dt_code using "$panel/panel_dataset_dd_nss.dta"

gen treat_x_post_int = treat_x_post * (HRS_dom_wide>=10) & (HRS_dom_wide!=.)
gen HRS = (HRS_dom_wide>=10) & (HRS_dom_wide!=.)


set obs 10000

global yvars = "elec_quantity log_elec_q elec_q_yn mth_pc_exp log_exp_30 mth_pc_expE1 log_exp_30E1 mth_pc_expE2 log_exp_30E2 " /// 
				+ "elec_light tv fan ac fridge"
global ytags = "none dec12 dec30" 

global ddvar_hrs_hi = "1.HRS#c.treat_x_post"
global ddvar_hrs_lo = "0.HRS#c.treat_x_post"
global ivvar = ""
global vce = "cluster clustvar"

gen panel = "district-year collapsed"
gen regs = "ols (HRS interaction)"
gen yvar = ""
gen ytag = ""
gen ddvar = ""
gen ivvar = ""
gen fes = ""
gen ifs = ""
gen vce = ""
gen beta_hrs_hi = .
gen se_hrs_hi = .
gen tscore_hrs_hi = .
gen pvalue_hrs_hi = .
gen ci95_lo_hrs_hi = .
gen ci95_hi_hrs_hi = .
gen beta_hrs_lo = .
gen se_hrs_lo = .
gen tscore_hrs_lo = .
gen pvalue_hrs_lo = .
gen ci95_lo_hrs_lo = .
gen ci95_hi_hrs_lo = .
gen pval_equal = .
gen ymean_pooled = .
gen ymean_2000 = .
gen ymean_2005 = .
gen ymean_hrs_hi = .
gen ymean_hrs_lo = .
gen nobs = .
gen nclust = .
gen r2 = .
gen fstat = .
gen rmse = .
gen row_id = .
local row_id = 1


foreach yvar in $yvars {
		
	foreach ytags in $ytags {
		
		if "`ytags'"=="none" {
			local ytag = ""
		}
		else {
			local ytag = "_`ytags'"
		}

		forvalues fes = 1/5 {
			
			if `fes'==1 {
				local fe = "year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt"
			}
			else if `fes'==2 {
				local fe = "year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt"
			}
			else if `fes'==3 {
				local fe = "year#HRS c.year#exp05_st_4ile#HRS c.year#exp05_ntl_10ile#HRS stdt#HRS"
			}
			else if `fes'==4 {
				local fe = "year#HRS c.year#exp05_st_4ile#HRS c.year#exp05_ntl_10ile#HRS c.year#st_code stdt#HRS"
			}
			else if `fes'==5 {
				local fe = "year#HRS c.year#exp05_st_4ile#HRS c.year#exp05_ntl_10ile#HRS c.year#st_code#HRS stdt#HRS"
			}
			
			foreach ifs in 1 {
			
				if `ifs'==1 {
					local if = ""
				}
		
				if !(("`if'"==" if year>2000") & (regexm("`ytag'","k") | substr("`tag'",-3,3)=="500")) {
					
					local ddvar_hrs_hi = "$ddvar_hrs_hi"
					local ddvar_hrs_lo = "$ddvar_hrs_lo"
					local ivvar = "$ivvar"
					local vce = "$vce"
					
					reghdfe `yvar'`ytag' `ddvar_hrs_hi' `ddvar_hrs_lo' `if' , a(`fe') vce(`vce')

					replace yvar = "`yvar'" in `row_id'
					replace ytag = "`ytag'" in `row_id'
					replace ddvar = "`ddvar'" in `row_id'
					replace ivvar = subinstr("`ivvar'",".","",1) in `row_id'
					replace fes = "`fe'" in `row_id'
					replace ifs = "`if'" in `row_id'
					replace vce = "`vce'" in `row_id'
					replace beta_hrs_hi = _b[`ddvar_hrs_hi'] in `row_id'
					replace se_hrs_hi = _se[`ddvar_hrs_hi'] in `row_id'
					replace tscore_hrs_hi = _b[`ddvar_hrs_hi']/_se[`ddvar_hrs_hi'] in `row_id'
					replace pvalue_hrs_hi = 2*ttail(e(df_r),abs(_b[`ddvar_hrs_hi']/_se[`ddvar_hrs_hi'])) in `row_id'
					replace ci95_lo_hrs_hi = _b[`ddvar_hrs_hi'] - _se[`ddvar_hrs_hi']*invttail(e(df_r),0.025) in `row_id'
					replace ci95_hi_hrs_hi = _b[`ddvar_hrs_hi'] + _se[`ddvar_hrs_hi']*invttail(e(df_r),0.025) in `row_id'
					replace beta_hrs_lo = _b[`ddvar_hrs_lo'] in `row_id'
					replace se_hrs_lo = _se[`ddvar_hrs_lo'] in `row_id'
					replace tscore_hrs_lo = _b[`ddvar_hrs_lo']/_se[`ddvar_hrs_lo'] in `row_id'
					replace pvalue_hrs_lo = 2*ttail(e(df_r),abs(_b[`ddvar_hrs_lo']/_se[`ddvar_hrs_lo'])) in `row_id'
					replace ci95_lo_hrs_lo = _b[`ddvar_hrs_lo'] - _se[`ddvar_hrs_lo']*invttail(e(df_r),0.025) in `row_id'
					replace ci95_hi_hrs_lo = _b[`ddvar_hrs_lo'] + _se[`ddvar_hrs_lo']*invttail(e(df_r),0.025) in `row_id'
					test `ddvar_hrs_hi'=`ddvar_hrs_lo'
					replace pval_equal = r(p) in `row_id'
					sum `yvar'`ytag' if e(sample)
					replace ymean_pooled = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & year==2000
					replace ymean_2000 = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & year==2005
					replace ymean_2005 = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & HRS==1
					replace ymean_hrs_hi = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & HRS==0
					replace ymean_hrs_lo = r(mean) in `row_id'
					replace nobs = e(N) in `row_id'
					replace nclust =  e(N_clust) in `row_id'
					replace r2 = e(r2) in `row_id'
					replace fstat = e(rkf) in `row_id'
					replace rmse = e(rmse) in `row_id'
					replace row_id = `row_id' in `row_id'
					local row_id = `row_id'+1
				}	
			}
		}
	}
}

keep panel-row_id
drop if _n>=`row_id'
tempfile newregs
save `newregs'
append using "$results/nss_reg_results.dta" `newregs'
duplicates drop
compress 
save "$results/nss_reg_results.dta", replace


}

********************************************************************************
********************************************************************************

** 7. Collapsed regressions, non-IV, Hours of power (split)
{
use "$panel/panel_dataset_full.dta", clear

	// Summarize hours of power to electrified villages, by district
egen temp1 = mean(vdp_pwr_h_all_avg) if vdp_pwr_h_all_avg_11>0, by(st_code dt_code)
egen HRS_all_wide = mode(temp1), by(st_code dt_code)
egen temp2 = mean(vdp_pwr_h_dom_avg) if vdp_pwr_h_dom_avg_11>0, by(st_code dt_code)
egen HRS_dom_wide = mode(temp2), by(st_code dt_code)
twoway scatter HRS_all_wide HRS_dom_wide

keep st_code dt_code HRS_all_wide HRS_dom_wide
duplicates drop
merge 1:m st_code dt_code using "$panel/panel_dataset_dd_nss.dta"

gen treat_x_post_int = treat_x_post * (HRS_dom_wide>=10) & (HRS_dom_wide!=.)
gen HRS = (HRS_dom_wide>=10) & (HRS_dom_wide!=.)


set obs 10000

global yvars = "elec_q_yn " 
global ytags = "none dec12 dec30" 

global ddvar = "treat_x_post"
global ivvar = ""
global vce = "cluster clustvar"
if "$ivvar"!="" {
	global vce = subinstr("$vce","cluster ","",1)
}

gen panel = "district-year collapsed"
gen regs = "ols (HRS splits)"
gen yvar = ""
gen ytag = ""
gen ddvar = ""
gen ivvar = ""
gen fes = ""
gen ifs = ""
gen vce = ""
gen beta = .
gen se = .
gen tscore = .
gen pvalue = .
gen ci95_lo = .
gen ci95_hi = .
gen ymean_pooled = .
gen ymean_2000 = .
gen ymean_2005 = .
gen ymean_2010_ctrl = .
gen nobs = .
gen nclust = .
gen r2 = .
gen fstat = .
gen rmse = .
gen row_id = .
local row_id = 1


foreach yvar in $yvars {
		
	foreach ytags in $ytags {
		
		if "`ytags'"=="none" {
			local ytag = ""
		}
		else {
			local ytag = "_`ytags'"
		}

		foreach fes in 1 {
			
			if `fes'==1 {
				local fe = "year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt"
			}
			
			foreach ifs in 1 2 {
			
				if `ifs'==1 {
					local if = " if HRS==1"
				}
				else if `ifs'==2 {
					local if = " if HRS==0"
				}

				if !(("`if'"==" if year>2000") & (regexm("`ytag'","k") | substr("`tag'",-3,3)=="500")) {
					
					local ddvar = "$ddvar"
					local ivvar = "$ivvar"
					local vce = "$vce"
					
					reghdfe `yvar'`ytag' `ddvar' `if' , a(`fe') vce(`vce')

					replace yvar = "`yvar'" in `row_id'
					replace ytag = "`ytag'" in `row_id'
					replace ddvar = "`ddvar'" in `row_id'
					replace ivvar = subinstr("`ivvar'",".","",1) in `row_id'
					replace fes = "`fe'" in `row_id'
					replace ifs = "`if'" in `row_id'
					replace vce = "`vce'" in `row_id'
					replace beta = _b[`ddvar'] in `row_id'
					replace se = _se[`ddvar'] in `row_id'
					replace tscore = _b[`ddvar']/_se[`ddvar'] in `row_id'
					replace pvalue = 2*ttail(e(df_r),abs(_b[`ddvar']/_se[`ddvar'])) in `row_id'
					replace ci95_lo = _b[`ddvar'] - _se[`ddvar']*invttail(e(df_r),0.025) in `row_id'
					replace ci95_hi = _b[`ddvar'] + _se[`ddvar']*invttail(e(df_r),0.025) in `row_id'
					sum `yvar'`ytag' if e(sample)
					replace ymean_pooled = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & year==2000
					replace ymean_2000 = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & year==2005
					replace ymean_2005 = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & year==2010 & `ddvar'==0
					replace ymean_2010_ctrl = r(mean) in `row_id'
					replace nobs = e(N) in `row_id'
					replace nclust =  e(N_clust) in `row_id'
					replace r2 = e(r2) in `row_id'
					replace fstat = e(rkf) in `row_id'
					replace rmse = e(rmse) in `row_id'
					replace row_id = `row_id' in `row_id'
					local row_id = `row_id'+1
				}	
			}
		}
	}
}

keep panel-row_id
drop if _n>=`row_id'
tempfile newregs
save `newregs'
append using "$results/nss_reg_results.dta" `newregs'
duplicates drop
compress 
save "$results/nss_reg_results.dta", replace


}

********************************************************************************
********************************************************************************

** 8. Collapsed regressions, IV, Hours of power (split)
{
use "$panel/panel_dataset_full.dta", clear

	// Summarize hours of power to electrified villages, by district
egen temp1 = mean(vdp_pwr_h_all_avg) if vdp_pwr_h_all_avg_11>0, by(st_code dt_code)
egen HRS_all_wide = mode(temp1), by(st_code dt_code)
egen temp2 = mean(vdp_pwr_h_dom_avg) if vdp_pwr_h_dom_avg_11>0, by(st_code dt_code)
egen HRS_dom_wide = mode(temp2), by(st_code dt_code)
twoway scatter HRS_all_wide HRS_dom_wide

keep st_code dt_code HRS_all_wide HRS_dom_wide
duplicates drop
merge 1:m st_code dt_code using "$panel/panel_dataset_dd_nss.dta"

gen treat_x_post_int = treat_x_post * (HRS_dom_wide>=10) & (HRS_dom_wide!=.)
gen HRS = (HRS_dom_wide>=10) & (HRS_dom_wide!=.)


set obs 10000

global yvars = "mth_pc_exp log_exp_30 mth_pc_expE1 log_exp_30E1 mth_pc_expE2 log_exp_30E2 tv " 
global ytags = "none dec12 dec30" 

global ddvar = "elec_q_yn"
global ivvar = "treat_x_post"
global vce = "cluster clustvar"
if "$ivvar"!="" {
	global vce = subinstr("$vce","cluster ","",1)
}

gen panel = "district-year collapsed"
gen regs = "iv (HRS splits)"
gen yvar = ""
gen ytag = ""
gen ddvar = ""
gen ivvar = ""
gen fes = ""
gen ifs = ""
gen vce = ""
gen beta = .
gen se = .
gen tscore = .
gen pvalue = .
gen ci95_lo = .
gen ci95_hi = .
gen ymean_pooled = .
gen ymean_2000 = .
gen ymean_2005 = .
gen ymean_2010_ctrl = .
gen nobs = .
gen nclust = .
gen r2 = .
gen fstat = .
gen rmse = .
gen row_id = .
local row_id = 1


foreach yvar in $yvars {
		
	foreach ytags in $ytags {
		
		if "`ytags'"=="none" {
			local ytag = ""
		}
		else {
			local ytag = "_`ytags'"
		}

		foreach fes in 1 {
			
			if `fes'==1 {
				local fe = "year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt"
			}
			
			foreach ifs in 1 2 {
			
				if `ifs'==1 {
					local if = " if HRS==1"
				}
				else if `ifs'==2 {
					local if = " if HRS==0"
				}

				if !(("`if'"==" if year>2000") & (regexm("`ytag'","k") | substr("`tag'",-3,3)=="500")) {
					
					local ddvar = "$ddvar`ytag'"
					local ivvar = "$ivvar"
					local vce = "$vce"
					
					ivreghdfe `yvar'`ytag' (`ddvar' = `ivvar') `if' , a(`fe') cluster(`vce')

					replace yvar = "`yvar'" in `row_id'
					replace ytag = "`ytag'" in `row_id'
					replace ddvar = "`ddvar'" in `row_id'
					replace ivvar = subinstr("`ivvar'",".","",1) in `row_id'
					replace fes = "`fe'" in `row_id'
					replace ifs = "`if'" in `row_id'
					replace vce = "`vce'" in `row_id'
					replace beta = _b[`ddvar'] in `row_id'
					replace se = _se[`ddvar'] in `row_id'
					replace tscore = _b[`ddvar']/_se[`ddvar'] in `row_id'
					replace pvalue = 2*ttail(e(df_r),abs(_b[`ddvar']/_se[`ddvar'])) in `row_id'
					replace ci95_lo = _b[`ddvar'] - _se[`ddvar']*invttail(e(df_r),0.025) in `row_id'
					replace ci95_hi = _b[`ddvar'] + _se[`ddvar']*invttail(e(df_r),0.025) in `row_id'
					sum `yvar'`ytag' if e(sample)
					replace ymean_pooled = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & year==2000
					replace ymean_2000 = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & year==2005
					replace ymean_2005 = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & year==2010 & `ivvar'==0
					replace ymean_2010_ctrl = r(mean) in `row_id'
					replace nobs = e(N) in `row_id'
					replace nclust =  e(N_clust) in `row_id'
					replace r2 = e(r2) in `row_id'
					replace fstat = e(rkf) in `row_id'
					replace rmse = e(rmse) in `row_id'
					replace row_id = `row_id' in `row_id'
					local row_id = `row_id'+1
					
				}	
			}
		}
	}
}

keep panel-row_id
drop if _n>=`row_id'
tempfile newregs
save `newregs'
append using "$results/nss_reg_results.dta" `newregs'
duplicates drop
compress 
save "$results/nss_reg_results.dta", replace


}

********************************************************************************
********************************************************************************

** 9. Collapsed regressions, non-IV, Hours of power (interacted, pre-trends)
{
use "$panel/panel_dataset_full.dta", clear

	// Summarize hours of power to electrified villages, by district
egen temp1 = mean(vdp_pwr_h_all_avg) if vdp_pwr_h_all_avg_11>0, by(st_code dt_code)
egen HRS_all_wide = mode(temp1), by(st_code dt_code)
egen temp2 = mean(vdp_pwr_h_dom_avg) if vdp_pwr_h_dom_avg_11>0, by(st_code dt_code)
egen HRS_dom_wide = mode(temp2), by(st_code dt_code)
twoway scatter HRS_all_wide HRS_dom_wide

keep st_code dt_code HRS_all_wide HRS_dom_wide
duplicates drop
merge 1:m st_code dt_code using "$panel/panel_dataset_dd_nss.dta"

gen treat_x_post_int = treat_x_post * (HRS_dom_wide>=10) & (HRS_dom_wide!=.)
gen HRS = (HRS_dom_wide>=10) & (HRS_dom_wide!=.)


set obs 10000

global yvars = "elec_quantity log_elec_q elec_q_yn mth_pc_exp log_exp_30 mth_pc_expE1 log_exp_30E1 mth_pc_expE2 log_exp_30E2 " /// 
				+ "elec_light tv fan ac fridge"
global ytags = "none dec12 dec30" 

global ddvar_hrs_hi = "1.HRS#c.treat_x_post05"
global ddvar_hrs_lo = "0.HRS#c.treat_x_post05"
global ivvar = ""
global vce = "cluster clustvar"

gen panel = "district-year collapsed"
gen regs = "ols (HRS interaction, pre-trends)"
gen yvar = ""
gen ytag = ""
gen ddvar = ""
gen ivvar = ""
gen fes = ""
gen ifs = ""
gen vce = ""
gen beta_hrs_hi = .
gen se_hrs_hi = .
gen tscore_hrs_hi = .
gen pvalue_hrs_hi = .
gen ci95_lo_hrs_hi = .
gen ci95_hi_hrs_hi = .
gen beta_hrs_lo = .
gen se_hrs_lo = .
gen tscore_hrs_lo = .
gen pvalue_hrs_lo = .
gen ci95_lo_hrs_lo = .
gen ci95_hi_hrs_lo = .
gen pval_equal = .
gen ymean_pooled = .
gen ymean_2000 = .
gen ymean_2005 = .
gen ymean_hrs_hi = .
gen ymean_hrs_lo = .
gen nobs = .
gen nclust = .
gen r2 = .
gen fstat = .
gen rmse = .
gen row_id = .
local row_id = 1


foreach yvar in $yvars {
		
	foreach ytags in $ytags {
		
		if "`ytags'"=="none" {
			local ytag = ""
		}
		else {
			local ytag = "_`ytags'"
		}

		foreach fes in 1 2 3 4 5 {
			
			if `fes'==1 {
				local fe = "year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt"
			}
			else if `fes'==2 {
				local fe = "year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt"
			}
			else if `fes'==3 {
				local fe = "year#HRS c.year#exp05_st_4ile#HRS c.year#exp05_ntl_10ile#HRS stdt#HRS"
			}
			else if `fes'==4 {
				local fe = "year#HRS c.year#exp05_st_4ile#HRS c.year#exp05_ntl_10ile#HRS c.year#st_code stdt#HRS"
			}
			else if `fes'==5 {
				local fe = "year#HRS c.year#exp05_st_4ile#HRS c.year#exp05_ntl_10ile#HRS c.year#st_code#HRS stdt#HRS"
			}
			
			foreach ifs in 1 {
			
				if `ifs'==1 {
					local if = " if year<2010"
				}
		
				if !(regexm("`ytag'","k") | substr("`tag'",-3,3)=="500") {
					
					local ddvar_hrs_hi = "$ddvar_hrs_hi"
					local ddvar_hrs_lo = "$ddvar_hrs_lo"
					local ivvar = "$ivvar"
					local vce = "$vce"
					
					reghdfe `yvar'`ytag' `ddvar_hrs_hi' `ddvar_hrs_lo' `if' , a(`fe') vce(`vce')

					replace yvar = "`yvar'" in `row_id'
					replace ytag = "`ytag'" in `row_id'
					replace ddvar = "`ddvar'" in `row_id'
					replace ivvar = subinstr("`ivvar'",".","",1) in `row_id'
					replace fes = "`fe'" in `row_id'
					replace ifs = "`if'" in `row_id'
					replace vce = "`vce'" in `row_id'
					replace beta_hrs_hi = _b[`ddvar_hrs_hi'] in `row_id'
					replace se_hrs_hi = _se[`ddvar_hrs_hi'] in `row_id'
					replace tscore_hrs_hi = _b[`ddvar_hrs_hi']/_se[`ddvar_hrs_hi'] in `row_id'
					replace pvalue_hrs_hi = 2*ttail(e(df_r),abs(_b[`ddvar_hrs_hi']/_se[`ddvar_hrs_hi'])) in `row_id'
					replace ci95_lo_hrs_hi = _b[`ddvar_hrs_hi'] - _se[`ddvar_hrs_hi']*invttail(e(df_r),0.025) in `row_id'
					replace ci95_hi_hrs_hi = _b[`ddvar_hrs_hi'] + _se[`ddvar_hrs_hi']*invttail(e(df_r),0.025) in `row_id'
					replace beta_hrs_lo = _b[`ddvar_hrs_lo'] in `row_id'
					replace se_hrs_lo = _se[`ddvar_hrs_lo'] in `row_id'
					replace tscore_hrs_lo = _b[`ddvar_hrs_lo']/_se[`ddvar_hrs_lo'] in `row_id'
					replace pvalue_hrs_lo = 2*ttail(e(df_r),abs(_b[`ddvar_hrs_lo']/_se[`ddvar_hrs_lo'])) in `row_id'
					replace ci95_lo_hrs_lo = _b[`ddvar_hrs_lo'] - _se[`ddvar_hrs_lo']*invttail(e(df_r),0.025) in `row_id'
					replace ci95_hi_hrs_lo = _b[`ddvar_hrs_lo'] + _se[`ddvar_hrs_lo']*invttail(e(df_r),0.025) in `row_id'
					test `ddvar_hrs_hi'=`ddvar_hrs_lo'
					replace pval_equal = r(p) in `row_id'
					sum `yvar'`ytag' if e(sample)
					replace ymean_pooled = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & year==2000
					replace ymean_2000 = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & year==2005
					replace ymean_2005 = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & HRS==1
					replace ymean_hrs_hi = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & HRS==0
					replace ymean_hrs_lo = r(mean) in `row_id'
					replace nobs = e(N) in `row_id'
					replace nclust =  e(N_clust) in `row_id'
					replace r2 = e(r2) in `row_id'
					replace fstat = e(rkf) in `row_id'
					replace rmse = e(rmse) in `row_id'
					replace row_id = `row_id' in `row_id'
					local row_id = `row_id'+1
				}	
			}
		}
	}
}

keep panel-row_id
drop if _n>=`row_id'
tempfile newregs
save `newregs'
append using "$results/nss_reg_results.dta" `newregs'
duplicates drop
compress 
save "$results/nss_reg_results.dta", replace


}

********************************************************************************
********************************************************************************

** 10. Collapsed regressions, endogenous second-stage OLS
{
use "$panel/panel_dataset_dd_nss.dta", clear
set obs 100000

global yvars = "mth_pc_exp log_exp_30 mth_pc_expE1 log_exp_30E1 mth_pc_expE2 log_exp_30E2 tv " //
				//+ "elec_light tv fan ac fridge"
global ytags = "none dec12 dec30"

global ddvar = "elec_q_yn"
global ivvar = ""
global vce = "cluster clustvar"

gen panel = "district-year collapsed"
gen regs = "ols (endogenous 2nd stage)"
gen yvar = ""
gen ytag = ""
gen ddvar = ""
gen ivvar = ""
gen fes = ""
gen ifs = ""
gen vce = ""
gen beta = .
gen se = .
gen tscore = .
gen pvalue = .
gen ci95_lo = .
gen ci95_hi = .
gen ymean_pooled = .
gen ymean_2000 = .
gen ymean_2005 = .
gen ymean_2010_ctrl = .
gen nobs = .
gen nclust = .
gen r2 = .
gen fstat = .
gen rmse = .
gen row_id = .
local row_id = 1

foreach yvar in $yvars {
		
	foreach ytags in $ytags {
		
		if "`ytags'"=="none" {
			local ytag = ""
		}
		else {
			local ytag = "_`ytags'"
		}

		forvalues fes = 1/6 {
			
			if `fes'==1 {
				local fe = "year stdt"
			}
			else if `fes'==2 {
				local fe = "year c.year#st_code stdt"
			}
			else if `fes'==3 {
				local fe = "year c.year#exp05_st_4ile stdt"
			}
			else if `fes'==4 {
				local fe = "year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt"
			}
			else if `fes'==5 {
				local fe = "year c.year#exp05_st_4ile c.year#st_code stdt"
			}
			else if `fes'==6 {
				local fe = "year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt"
			}
			
			forvalues ifs = 1/5 {
			
				if `ifs'==1 {
					local if = ""
				}
				else if `ifs'==2 {
					local if = " if year>2000"
				}
				else if `ifs'==3 {
					local if = " if sample_1011"
				}
				else if `ifs'==4 {
					local if = " if flag_91_match_iffy==0"
				}
				else if `ifs'==5 {
					local if = " if flag_91dist_split==0"
				}
		
				if !(("`if'"==" if year>2000") & (regexm("`ytag'","k") | substr("`tag'",-3,3)=="500")) {
					
					local ddvar = "$ddvar"
					local ivvar = "$ivvar"
					local vce = "$vce"
					
					reghdfe `yvar'`ytag' `ddvar' `if' , a(`fe') vce(`vce')

					replace yvar = "`yvar'" in `row_id'
					replace ytag = "`ytag'" in `row_id'
					replace ddvar = "`ddvar'" in `row_id'
					replace ivvar = subinstr("`ivvar'",".","",1) in `row_id'
					replace fes = "`fe'" in `row_id'
					replace ifs = "`if'" in `row_id'
					replace vce = "`vce'" in `row_id'
					replace beta = _b[`ddvar'] in `row_id'
					replace se = _se[`ddvar'] in `row_id'
					replace tscore = _b[`ddvar']/_se[`ddvar'] in `row_id'
					replace pvalue = 2*ttail(e(df_r),abs(_b[`ddvar']/_se[`ddvar'])) in `row_id'
					replace ci95_lo = _b[`ddvar'] - _se[`ddvar']*invttail(e(df_r),0.025) in `row_id'
					replace ci95_hi = _b[`ddvar'] + _se[`ddvar']*invttail(e(df_r),0.025) in `row_id'
					sum `yvar'`ytag' if e(sample)
					replace ymean_pooled = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & year==2000
					replace ymean_2000 = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & year==2005
					replace ymean_2005 = r(mean) in `row_id'
					sum `yvar'`ytag' if e(sample) & year==2010 & `ddvar'==0
					replace ymean_2010_ctrl = r(mean) in `row_id'
					replace nobs = e(N) in `row_id'
					replace nclust =  e(N_clust) in `row_id'
					replace r2 = e(r2) in `row_id'
					replace fstat = e(rkf) in `row_id'
					replace rmse = e(rmse) in `row_id'
					replace row_id = `row_id' in `row_id'
					local row_id = `row_id'+1
				}	
			}
		}
	}
}

keep panel-row_id
drop if _n>=`row_id'
tempfile newregs
save `newregs'
append using "$results/nss_reg_results.dta" `newregs'
duplicates drop
compress 
save "$results/nss_reg_results.dta", replace

}

********************************************************************************
********************************************************************************

** 11. Uncollapsed regressions, first-stage expenditure splits for consumer surplus calculations
{
	// start with UNCOLLAPSED NSS panel, since we're explicitly splitting on expenditure in levels
use "$panel/panel_dataset_dd_nss_uncollapsed.dta", clear

	// create nationally representative weights, for internal consistency
gen weight_pop = weight_normalized * tot_p_dist

	// create expenditure quartiles (variable is already inflated to 2010 rupees, E1 = less electricity expenditure)
sum mth_pc_expE1 [aw=weight_pop], detail
gen exp_quartile = .
replace exp_quartile = 1 if mth_pc_expE1<=r(p25)
replace exp_quartile = 2 if mth_pc_expE1<=r(p50) & exp_quartile==.
replace exp_quartile = 3 if mth_pc_expE1<=r(p75) & exp_quartile==.
replace exp_quartile = 4 if exp_quartile==.
global q1_cap = r(p25)
global q2_cap = r(p50)
global q3_cap = r(p75)
global q4_cap = r(max)

global yvars = "elec_quantity elec_q_yn"
			 
global ddvar = "treat_x_post"
global ivvar = ""
global vce = "cluster stdt_cluster"
global weight = "aw=weight_pop"
global fe = "year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt"

gen panel = "district-year uncollapsed"
gen regs = "ols, uncollapsed"
gen yvar = ""
gen ytag = ""
gen ddvar = ""
gen ivvar = ""
gen fes = ""
gen ifs = ""
gen weight = ""
gen vce = ""
gen beta = .
gen se = .
gen tscore = .
gen pvalue = .
gen ci95_lo = .
gen ci95_hi = .
gen ymean_pooled = .
gen ymean_2000 = .
gen ymean_2005 = .
gen ymean_2010_ctrl = .
gen nobs = .
gen nclust = .
gen r2 = .
gen fstat = .
gen rmse = .
gen exp_cap = .
gen row_id = .
local row_id = 1

foreach yvar in $yvars {
		
	foreach yifs in 1 2 3 4 {
		
		local if = " if exp_quartile==`yifs'"
							
		local ddvar = "$ddvar"
		local ivvar = "$ivvar"
		local fe = "$fe"
		local weight = "$weight"
		local vce = "$vce"
		
		reghdfe `yvar' `ddvar' `if' [`weight'], a(`fe') vce(`vce')

		replace yvar = "`yvar'" in `row_id'
		replace ytag = "" in `row_id'
		replace ddvar = "`ddvar'" in `row_id'
		replace ivvar = subinstr("`ivvar'",".","",1) in `row_id'
		replace fes = "`fe'" in `row_id'
		replace ifs = "`if'" in `row_id'
		replace weight = "`weight'" in `row_id'
		replace vce = "`vce'" in `row_id'
		replace beta = _b[`ddvar'] in `row_id'
		replace se = _se[`ddvar'] in `row_id'
		replace tscore = _b[`ddvar']/_se[`ddvar'] in `row_id'
		replace pvalue = 2*ttail(e(df_r),abs(_b[`ddvar']/_se[`ddvar'])) in `row_id'
		replace ci95_lo = _b[`ddvar'] - _se[`ddvar']*invttail(e(df_r),0.025) in `row_id'
		replace ci95_hi = _b[`ddvar'] + _se[`ddvar']*invttail(e(df_r),0.025) in `row_id'
		sum `yvar' if e(sample)
		replace ymean_pooled = r(mean) in `row_id'
		sum `yvar' if e(sample) & year==2000
		replace ymean_2000 = r(mean) in `row_id'
		sum `yvar' if e(sample) & year==2005
		replace ymean_2005 = r(mean) in `row_id'
		sum `yvar' if e(sample) & year==2010 & `ddvar'==0
		replace ymean_2010_ctrl = r(mean) in `row_id'
		replace nobs = e(N) in `row_id'
		replace nclust =  e(N_clust) in `row_id'
		replace r2 = e(r2) in `row_id'
		replace fstat = e(rkf) in `row_id'
		replace rmse = e(rmse) in `row_id'
		replace exp_cap = ${q`yifs'_cap} in `row_id'
		sum `yvar' if e(sample)
		replace row_id = `row_id' in `row_id'
		local row_id = `row_id'+1
	}
}

keep panel-row_id
drop if _n>=`row_id'
tempfile newregs
save `newregs'
append using "$results/nss_reg_results.dta" `newregs'
duplicates drop
compress 
save "$results/nss_reg_results.dta", replace

}

********************************************************************************
********************************************************************************

