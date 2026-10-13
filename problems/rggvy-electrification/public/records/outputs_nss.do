clear all
set more off, perm
set mem 10000000
set matsize 10000
version 13

*********************************************************** 
*** Table and figures for JPE revisions: NSS DD results ***
*********************************************************** 

** Set file paths
do "$path_code/paths.do"

** Set graph scheme
cd "$path/code/analyze"
set scheme fb, perm

********************************************************************************
********************************************************************************

** Table 3: NSS first-stage DD, extensive and intensive margins + appliances
{
cap file close tablewrite
use "$results/nss_reg_results.dta", clear
keep if panel=="district-year collapsed"
keep if regs=="ols"
keep if inlist(yvar,"elec_q_yn","log_elec_q","elec_quantity","elec_light","fan","tv","fridge","ac")
keep if ytag==""
keep if ifs==""
keep if inlist(fes,"year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt")

gen c = .
replace c = 1 if yvar=="elec_q_yn"	
replace c = 2 if yvar=="elec_quantity" 
replace c = 3 if yvar=="log_elec_q"
replace c = 4 if yvar=="elec_light"
replace c = 5 if yvar=="fan" 
replace c = 6 if yvar=="tv" 
replace c = 7 if yvar=="fridge"
replace c = 8 if yvar=="ac" 	
assert c!=.	
sort c

forvalues c = 1/8 {
	
	if `c'!=2 {
		local beta`c' = string(beta[`c'],"%9.3f")
		local se`c' = string(se[`c'],"%9.3f")
	}
	else {
	    local beta`c' = string(beta[`c'],"%9.2f")
		local se`c' = string(se[`c'],"%9.2f")
	}
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if  pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}

	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']
	if `c'!=2 {
		local ymean`c' = string(ymean_pooled[`c'],"%9.3f")
	}
	else {
		local ymean`c' = string(ymean_pooled[`c'],"%9.2f")    
	}
}	
	
   // MAKE TABLE
file open tablewrite using "$textab/table_nss_first_stage.tex", write text replace
 
file write tablewrite "\begin{table}[p]\centering" _n
file write tablewrite "\caption{District-level DD of household electricity access and usage}" _n
file write tablewrite "\label{tab:nss_first_stage}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\small" _n
file write tablewrite "\begin{tabular}{lccccccccccc}" _n
file write tablewrite "\hline" _n
file write tablewrite "& \multicolumn{3}{c}{HH elec use (kWh/month)} "  _n
file write tablewrite "&& \multicolumn{5}{c}{\$ \mathbf{1}\big[\text{HH owns electric appliance}\big] \$} \\ "  _n
file write tablewrite "\cline{2-4} \cline{6-10}\\" _n
file write tablewrite "\vspace{-0.90cm}" _n
file write tablewrite "\\" _n
file write tablewrite "& \$ \mathbf{1}\big[Q > 0\big] \$ & Levels & Logs && Lighting & Fan & TV & Fridge & AC \\" _n
file write tablewrite "& (1) & (2) & (3) && (4) & (5) & (6) & (7) & (8) \\" _n
file write tablewrite "\hline" _n
file write tablewrite "\vspace{-0.40cm}" _n
file write tablewrite "\\" _n
file write tablewrite "$\mathbf{1}\big[\text{10th-Plan}\big] \$ & " _n
file write tablewrite "$`beta1'$`stars1' & $`beta2'$`stars2' & $`beta3'$`stars3' && $`beta4'$`stars4' & $`beta5'$`stars5' & $`beta6'$`stars6' & $`beta7'$`stars7' & $`beta8'$`stars8' \\" _n
file write tablewrite "$ ~~\times \, \mathbf{1}\big[2010\big] \$ & $(`se1')$ & $(`se2')$ & $(`se3')$ && $(`se4')$ & $(`se5')$ & $(`se6')$  & $(`se7')$  & $(`se8')$ \\" _n
file write tablewrite "[0.8em]" _n
file write tablewrite "Mean of dep var & `ymean1' & `ymean2' & `ymean3' && `ymean4' & `ymean5' & `ymean6' & `ymean7' & `ymean8' \\" _n
file write tablewrite "Clusters & `nclust1' & `nclust2' & `nclust3' && `nclust4' & `nclust5' & `nclust6' & `nclust7' & `nclust8' \\" _n
file write tablewrite "Observations & `nobs1' & `nobs2' & `nobs3' && `nobs4' & `nobs5' & `nobs6' & `nobs7' & `nobs8' \\" _n
file write tablewrite "\hline" _n
file write tablewrite "\end{tabular}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\caption*{\scriptsize Note. --- District-level DD with three NSS years (2000, 2005, 2010). " _n
file write tablewrite "We aggregate household-level data up to the district using sampling weights, for rural households only. " _n
file write tablewrite "Outcome variables are an indicator for whether a household consumed any electricity (Column (1)), " _n
file write tablewrite "monthly household electricity consumption in levels and in natural logs (Columns (2)--(3)),  " _n
file write tablewrite "and indicators for whether a household owned electric lighting, an electric fan, " _n
file write tablewrite "a television, a refrigerator, or air conditioning (Columns (4)--(8)). " _n
file write tablewrite "DD treatment is assigned at the district level, for 10th-Plan districts. " _n
file write tablewrite "All regressions include: district fixed effects; year fixed effects; state-specific linear trends; " _n
file write tablewrite "linear trends in state quartiles of 2005 household expenditures per capita, " _n 
file write tablewrite "to control for within-state selection in RGGVY implementation based on relative differences between " _n
file write tablewrite "districts (e.g.\ states prioritizing electrification in their poorest districts); " _n
file write tablewrite "and linear trends in national deciles of 2005 household expenditures per capita control for " _n
file write tablewrite "such selection in absolute terms. Standard errors are clustered at the district level, " _n
file write tablewrite "collapsing to a single cluster for (i) districts that split in the 2001 Census, but which " _n
file write tablewrite "the 2000 NSS sampled based on 1991 district definitions; and (ii) the few cases where an RGGVY " _n
file write tablewrite "DPR included multiple districts." _n
file write tablewrite "Significance: *** \$p < 0.01\$, ** \$p < 0.05\$, * \$p < 0.10\$." _n
file write tablewrite "}" _n
file write tablewrite "\end{table}" _n

file close tablewrite

}

********************************************************************************
********************************************************************************

** Table 5: NSS reduced-form DD, levels and logs
{
cap file close tablewrite
use "$results/nss_reg_results.dta", clear
keep if panel=="district-year collapsed"
keep if regs=="ols"
keep if inlist(yvar,"mth_pc_expE1","log_exp_30E1")
keep if ytag==""
keep if ifs==""
keep if inlist(fes,"year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt")

gen c = .
replace c = 1 if yvar=="mth_pc_expE1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt"	
replace c = 2 if yvar=="log_exp_30E1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt"	
assert c!=.	
sort c

forvalues c = 1/1 {
		
	local beta`c' = string(beta[`c'],"%9.2f")
	local se`c' = string(se[`c'],"%9.2f")
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if  pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}

	local ymean`c' = string(ymean_pooled[`c'],"%9.2f")
	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']
}	
	
forvalues c = 2/2 {

	local beta`c' = string(beta[`c'],"%9.3f")
	local se`c' = string(se[`c'],"%9.3f")
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if  pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}

	local ymean`c' = string(ymean_pooled[`c'],"%9.3f")
	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']
}
	
   // MAKE TABLE
file open tablewrite using "$textab/table_nss_reduced_form.tex", write text replace
 
file write tablewrite "\begin{table}[p]\centering" _n
file write tablewrite "\caption{District-level DD of household consumption expenditures}" _n
file write tablewrite "\label{tab:nss_reduced_form}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\small " _n
file write tablewrite "\begin{tabular}{lccccccccc}" _n
file write tablewrite "\hline" _n
file write tablewrite "& \multicolumn{3}{c}{Expenditure per capita (Rs/month)}  \\ " _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\cline{2-4}\\" _n
file write tablewrite "\vspace{-0.90cm}" _n
file write tablewrite "\\" _n
file write tablewrite "& \multicolumn{1}{c}{~~~~~~~~~~Levels~~~~~~~~~~} & " _n
file write tablewrite "& \multicolumn{1}{c}{Logs} \\" _n
file write tablewrite "& (1) & & (2) \\" _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\hline" _n
file write tablewrite "\vspace{-0.20cm}" _n
file write tablewrite "\\" _n
file write tablewrite "$\mathbf{1}\big[\text{10th-Plan}\big] \times \mathbf{1}\big[2010\big]$ & " _n
file write tablewrite "$`beta1'$`stars1' && $`beta2'$`stars2' \\" _n
file write tablewrite "& $(`se1')$ && $(`se2')$  \\" _n
file write tablewrite "[0.8em]" _n
file write tablewrite "Mean of dep var & `ymean1' && `ymean2' \\" _n
file write tablewrite "Clusters & `nclust1' && `nclust2'  \\" _n
file write tablewrite "Observations & `nobs1' && `nobs2' \\" _n
file write tablewrite "\hline" _n
file write tablewrite "\end{tabular}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\caption*{\scriptsize Note. --- District-level DD with three NSS years (2000, 2005, 2010). " _n
file write tablewrite "The outcome variable is total household expenditures per capita (net of electricity spending " _n
file write tablewrite "per capita), over the 30-day period period prior to survey enumeration, " _n
file write tablewrite "in 2010 rupees per month (Column (1)) and log-transformed (Column (2)). " _n
file write tablewrite "Both regressions include: district fixed effects; year fixed effects; state-specific linear trends;  " _n
file write tablewrite "linear trends in state quartiles of 2005 household expenditures per capita; " _n 
file write tablewrite "and linear trends in national deciles of 2005 household expenditures per capita. " _n
file write tablewrite "See notes under Table \ref{tab:nss_first_stage} for further details. " _n
file write tablewrite "Standard errors are clustered at the district level, collapsing to a " _n
file write tablewrite "single cluster for (i) districts that split in the 2001 Census, but which " _n
file write tablewrite "the 2000 NSS sampled based on 1991 district definitions; and (ii) the few cases " _n
file write tablewrite "where an RGGVY DPR included multiple districts." _n
file write tablewrite "Significance: *** \$p < 0.01\$, ** \$p < 0.05\$, * \$p < 0.10\$." _n
file write tablewrite "}" _n
file write tablewrite "\end{table}" _n

file close tablewrite

}

********************************************************************************
********************************************************************************

** Table 7: NSS 2SLS DD, levels and logs
{
cap file close tablewrite
use "$results/nss_reg_results.dta", clear
keep if panel=="district-year collapsed"
keep if (regs=="iv" & inlist(yvar,"mth_pc_expE1","log_exp_30E1")) | (regs=="ols" & inlist(yvar,"elec_q_yn"))
keep if inlist(ytag,"","_dec12","_dec30")
keep if ifs==""
keep if inlist(fes,"year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt")

gen c = .
replace c = 1 if yvar=="mth_pc_expE1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag==""
replace c = 2 if yvar=="mth_pc_expE1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_dec12"
replace c = 3 if yvar=="mth_pc_expE1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_dec30"
replace c = 4 if yvar=="log_exp_30E1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag==""
replace c = 5 if yvar=="log_exp_30E1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_dec12"
replace c = 6 if yvar=="log_exp_30E1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_dec30"
replace c = 7 if yvar=="elec_q_yn" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag==""
replace c = 8 if yvar=="elec_q_yn" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_dec12"
replace c = 9 if yvar=="elec_q_yn" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_dec30"
assert c!=.	
sort c

forvalues c = 1/3 {
		
	local beta`c' = string(beta[`c'],"%9.1f")
	local se`c' = string(se[`c'],"%9.1f")
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if  pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}
	
	local lci`c' = string(ci95_lo[`c'],"%9.1f")
	local uci`c' = string(ci95_hi[`c'],"%9.1f")
	local ymean`c' = string(ymean_pooled[`c'],"%9.1f")

	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']
	local fstat`c' = string(fstat[`c'],"%9.2f")
}	
	
forvalues c = 4/6 {

	local beta`c' = string(beta[`c'],"%9.3f")
	local se`c' = string(se[`c'],"%9.3f")
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if  pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}

	local lci`c' = string(ci95_lo[`c'],"%9.3f")
	local uci`c' = string(ci95_hi[`c'],"%9.3f")
	local ymean`c' = string(ymean_pooled[`c'],"%9.3f")

	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']
	local fstat`c' = string(fstat[`c'],"%9.2f")
}

forvalues c = 7/9 {

	local beta`c' = string(beta[`c'],"%9.3f")
	local se`c' = string(se[`c'],"%9.3f")
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if  pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}
}

	
use "$panel/panel_dataset_dd_nss_uncollapsed.dta", clear
egen vill_tag = tag(fsu_serial st_code dt_code year)
sum frame_pop if vill_tag, detail
local pop_p50_0 = string(r(p50),"%9.0f")
local pop_p90_0 = string(r(p90),"%9.0f")
sum frame_pop if inrange(WT_decile,1,2) & vill_tag, detail
local pop_p50_1 = string(r(p50),"%9.0f")
local pop_p90_1 = string(r(p90),"%9.0f")
sum frame_pop if inrange(WT_decile,3,10) & vill_tag, detail
local pop_p50_2 = string(r(p50),"%9.0f")
local pop_p90_2 = string(r(p90),"%9.0f")


   // MAKE TABLE
file open tablewrite using "$textab/table_nss_2sls.tex", write text replace
 
file write tablewrite "\begin{table}[p]\centering" _n
file write tablewrite "\caption{District-level DD-IV of household consumption expenditures}" _n
file write tablewrite "\label{tab:nss_2sls}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\small" _n
file write tablewrite "\begin{tabular}{lccccccccc}" _n
file write tablewrite "\hline" _n
file write tablewrite "& \multicolumn{7}{c}{Expenditure per capita (Rs/month)}  \\ " _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\cline{2-8}\\" _n
file write tablewrite "\vspace{-0.90cm}" _n
file write tablewrite "\\" _n
file write tablewrite "& \multicolumn{3}{c}{Levels} & " _n
file write tablewrite "& \multicolumn{3}{c}{Logs} \\" _n
file write tablewrite "& (1) & (2) & (3) && (4) & (5) & (6) \\" _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\cline{2-4} \cline{6-8}" _n
file write tablewrite "\vspace{-0.20cm}" _n
file write tablewrite "\\" _n
file write tablewrite "\$ \mathbf{1}\big[\text{HH consumes any elec}\big] \$ & " _n
file write tablewrite "$`beta1'$`stars1' & $`beta2'$`stars2' & $`beta3'$`stars3' && $`beta4'$`stars4' & $`beta5'$`stars5' & $`beta6'$`stars6' \\" _n
file write tablewrite "& $(`se1')$ & $(`se2')$ & $(`se3')$ && $(`se4')$ & $(`se5')$ & $(`se6')$ \\" _n
file write tablewrite "[0.8em]" _n
file write tablewrite "95\% confidence & \$[`lci1'\$, & \$[`lci2'\$, & \$[`lci3'\$, && \$[`lci4'\$, & \$[`lci5'\$, & \$[`lci6'\$, \\" _n 
file write tablewrite "& \$~`uci1']\$  & \$~`uci2']\$  & \$~`uci3']\$  && \$~`uci4']\$  & \$~`uci5']\$  & \$~`uci6']\$  \\ " _n 
file write tablewrite "[0.8em]" _n
file write tablewrite "Village weight quintiles & Pooled & 1 & 2--5 && Pooled & 1 & 2--5 \\" _n
file write tablewrite "50th pctile of 2001 pop & `pop_p50_0' & `pop_p50_1' & `pop_p50_2' && `pop_p50_0' & `pop_p50_1' & `pop_p50_2' \\" _n
file write tablewrite "90th pctile of 2001 pop & `pop_p90_0' & `pop_p90_1' & `pop_p90_2' && `pop_p90_0' & `pop_p90_1' & `pop_p90_2' \\" _n
file write tablewrite "[0.8em]" _n
file write tablewrite "Mean of dep var & `ymean1' & `ymean2' & `ymean3' && `ymean4' & `ymean5' & `ymean6' \\" _n
file write tablewrite "Clusters & `nclust1' & `nclust2' & `nclust3' && `nclust4' & `nclust5' & `nclust6' \\" _n
file write tablewrite "Observations & `nobs1' & `nobs2' & `nobs3' && `nobs4' & `nobs5' & `nobs6' \\" _n
file write tablewrite "[0.3em]" _n
file write tablewrite "\hline" _n
file write tablewrite "\vspace{-3mm}" _n
file write tablewrite "\\" _n
file write tablewrite "First-stage estimate &  " _n
file write tablewrite "$`beta7'$`stars7' & $`beta8'$`stars8' & $`beta9'$`stars9' && $`beta7'$`stars7' & $`beta8'$`stars8' & $`beta9'$`stars9' \\" _n
file write tablewrite "~~(standard error) & $(`se7')$ & $(`se8')$ & $(`se9')$ && $(`se7')$ & $(`se8')$ & $(`se9')$ \\" _n
file write tablewrite "[0.5em]"
file write tablewrite "First-stage \$F\$-statistic & `fstat1' & `fstat2' & `fstat3' && `fstat4' & `fstat5' & `fstat6' \\" _n
file write tablewrite "\hline" _n
file write tablewrite "\end{tabular}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\caption*{\scriptsize Note. --- District-level DD with three NSS years (2000, 2005, 2010), " _n
file write tablewrite "estimated via two-stage least squares. We instrument for household electricity access " _n
file write tablewrite "with the interaction \$\mathbf{1}\big[\text{10th-Plan district}\big] \times \mathbf{1}\big[2010\big]\$. " _n 
file write tablewrite "The outcome variable is net of per capita spending on electricity. " _n
file write tablewrite "Columns (2)--(3) and (5)--(6) split the sample on within-year quintiles of NSS village weights " _n
file write tablewrite "before collapsing to the district level using sampling weights. " _n
file write tablewrite "We do not observe village populations for the 2000 NSS wave, meaning that we cannot estimate a 3-period panel " _n
file write tablewrite "splitting directly on village size. However, isolating the first quintile of NSS sampling weights shifts the " _n
file write tablewrite "distribution of 2001 village populations (as observed in 2005 and 2010 waves) towards smaller villages.   " _n
file write tablewrite "All regressions include: district fixed effects; year fixed effects; " _n
file write tablewrite "linear trends in state quartiles of 2005 household expenditures per capita; " _n 
file write tablewrite "and linear trends in national deciles of 2005 household expenditures per capita. " _n
file write tablewrite "See notes under Table \ref{tab:nss_first_stage} for further details. " _n
file write tablewrite "Standard errors are clustered at the district level, collapsing to a " _n
file write tablewrite "single cluster for (i) districts that split in the 2001 Census, but which " _n
file write tablewrite "the 2000 NSS sampled based on 1991 district definitions; and (ii) the few cases " _n
file write tablewrite "where an RGGVY DPR included multiple districts." _n
file write tablewrite "The bottom three rows report the first-stage point estimates and standard errors, and " _n
file write tablewrite "Kleibergen-Paap first-stage \$F\$-statistics. " _n
file write tablewrite "Significance: *** \$p < 0.01\$, ** \$p < 0.05\$, * \$p < 0.10\$." _n
file write tablewrite "}" _n
file write tablewrite "\end{table}" _n

file close tablewrite

}

********************************************************************************
********************************************************************************

** Table A6: NSS first-stage DD, extensive and intensive margins, no state-specific trends 
{
cap file close tablewrite
use "$results/nss_reg_results.dta", clear
keep if panel=="district-year collapsed"
keep if regs=="ols"
keep if inlist(yvar,"elec_q_yn","log_elec_q","elec_quantity")
keep if ytag==""
keep if ifs==""
keep if inlist(fes,"year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt")

gen c = .
replace c = 1 if yvar=="elec_q_yn"	
replace c = 2 if yvar=="elec_quantity" 
replace c = 3 if yvar=="log_elec_q"
assert c!=.	
sort c

forvalues c = 1/3 {
	
	if `c'!=2 {
		local beta`c' = string(beta[`c'],"%9.3f")
		local se`c' = string(se[`c'],"%9.3f")
	}
	else {
	    local beta`c' = string(beta[`c'],"%9.2f")
		local se`c' = string(se[`c'],"%9.2f")
	}
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if  pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}

	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']
	if `c'!=2 {
		local ymean`c' = string(ymean_pooled[`c'],"%9.3f")
	}
	else {
		local ymean`c' = string(ymean_pooled[`c'],"%9.2f")    
	}
}	
	
   // MAKE TABLE
file open tablewrite using "$textab/table_nss_first_stage_no_state_trends.tex", write text replace
 
file write tablewrite "\begin{table}[h!]\centering" _n
file write tablewrite "\caption{District-level DD, NSS variables, without state-specific linear trends}" _n
file write tablewrite "\label{tab:nss_first_stage_no_state_trends}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\small" _n
file write tablewrite "\begin{tabular}{lccccccccccc}" _n
file write tablewrite "\hline" _n
file write tablewrite "& \multicolumn{3}{c}{HH electricity use (kWh/month)} \\ "  _n
file write tablewrite "\cline{2-4}\\" _n
file write tablewrite "\vspace{-0.90cm}" _n
file write tablewrite "\\" _n
file write tablewrite "& ~~\$ \mathbf{1}\big[Q > 0\big] \$~~ & ~~Levels~~ & Logs \\" _n
file write tablewrite "& (1) & (2) & (3) \\" _n
file write tablewrite "\hline" _n
file write tablewrite "\vspace{-0.40cm}" _n
file write tablewrite "\\" _n
file write tablewrite "$\mathbf{1}\big[\text{10th-Plan district}\big] \times \, \mathbf{1}\big[2010\big] \$~~ & " _n
file write tablewrite "$`beta1'$`stars1' & $`beta2'$`stars2' & $`beta3'$`stars3' \\" _n
file write tablewrite "& $(`se1')$ & $(`se2')$ & $(`se3')$ \\" _n
file write tablewrite "[0.8em]" _n
file write tablewrite "Mean of dep var & `ymean1' & `ymean2' & `ymean3' \\" _n
file write tablewrite "Clusters & `nclust1' & `nclust2' & `nclust3' \\" _n
file write tablewrite "Observations & `nobs1' & `nobs2' & `nobs3' \\" _n
file write tablewrite "\hline" _n
file write tablewrite "\end{tabular}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\caption*{\scriptsize Note. --- Regressions are identical to Columns (1)--(3) of " _n
file write tablewrite "Table \ref*{tab:nss_first_stage}, except that they remove state-specific linear trends. " _n
file write tablewrite "All regressions include: district fixed effects; year fixed effects; " _n
file write tablewrite "linear trends in state quartiles of 2005 household expenditures per capita; " _n 
file write tablewrite "and linear trends in national deciles of 2005 household expenditures per capita. " _n
file write tablewrite "Standard errors are clustered at the district level, collapsing to a " _n
file write tablewrite "single cluster for (i) districts that split in the 2001 Census, but which " _n
file write tablewrite "the 2000 NSS sampled based on 1991 district definitions; and (ii) the few cases " _n
file write tablewrite "where an RGGVY DPR included multiple districts." _n
file write tablewrite "Significance: *** \$p < 0.01\$, ** \$p < 0.05\$, * \$p < 0.10\$." _n
file write tablewrite "}" _n
file write tablewrite "\end{table}" _n

file close tablewrite

}

********************************************************************************
********************************************************************************

** Table A7: NSS first-stage DD, extensive and intensive (above/below 2000 people)
{
cap file close tablewrite
use "$results/nss_reg_results.dta", clear
keep if panel=="district-year collapsed"
keep if regs=="ols"
keep if inlist(yvar,"elec_q_yn","log_elec_q","elec_quantity")
keep if inlist(ytag,"_under2k","_over2k")
keep if ifs==""
keep if inlist(fes,"year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt")

gen c = .
replace c = 1 if yvar=="elec_q_yn" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_under2k"
replace c = 2 if yvar=="elec_q_yn" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_over2k"	
replace c = 3 if yvar=="elec_quantity" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_under2k"
replace c = 4 if yvar=="elec_quantity" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_over2k"
replace c = 5 if yvar=="log_elec_q"  & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_under2k"
replace c = 6 if yvar=="log_elec_q" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_over2k"
assert c!=.	
sort c

forvalues c = 1/6 {
		
	if inlist(`c',3,4) {
	    local beta`c' = string(beta[`c'],"%9.2f")
		local se`c' = string(se[`c'],"%9.2f")
	}
	else {
	    local beta`c' = string(beta[`c'],"%9.3f")
		local se`c' = string(se[`c'],"%9.3f")	    
	}
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if  pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}

	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']
	if inlist(`c',3,4) {
	    local ymean`c' = string(ymean_pooled[`c'],"%9.2f")
	}
	else {
	    local ymean`c' = string(ymean_pooled[`c'],"%9.3f")	    
	}
}	

	
   // MAKE TABLE
file open tablewrite using "$textab/table_nss_first_stage_2k_pop.tex", write text replace
 
file write tablewrite "\begin{table}[p]\centering" _n
file write tablewrite "\caption{District-level DD split by 2001 village population}" _n
file write tablewrite "\label{tab:nss_first_stage_2k_pop}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\small" _n
file write tablewrite "\begin{tabular}{lccccccccc}" _n
file write tablewrite "\hline" _n
file write tablewrite "& \multicolumn{2}{c}{\$ \mathbf{1}\big[\text{kWh} > 0\big] \$} & "  _n
file write tablewrite "& \multicolumn{2}{c}{\$ \text{kWh/month} \$} & " _n
file write tablewrite "& \multicolumn{2}{c}{\$ \log\big(\text{kWh/month}\big) \$} \\" _n
file write tablewrite "[0.2em]" _n
file write tablewrite "& (1) & (2) && (3) & (4) && (5) & (6) \\" _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\cline{2-3} \cline{5-6} \cline{8-9}\\" _n
file write tablewrite "\vspace{-0.80cm}" _n
file write tablewrite "\\" _n
file write tablewrite "$\mathbf{1}\big[\text{10th-Plan district}\big] \times \mathbf{1}\big[2010\big]$~~ & " _n
file write tablewrite "$`beta1'$`stars1' & $`beta2'$`stars2' && $`beta3'$`stars3' & $`beta4'$`stars4' && $`beta5'$`stars5' & $`beta6'$`stars6' \\" _n
file write tablewrite "& $(`se1')$ & $(`se2')$ && $(`se3')$ & $(`se4')$ && $(`se5')$ & $(`se6')$ \\" _n
file write tablewrite "[0.8em]" _n
file write tablewrite "2001 village population split~ & $\le2000$ & $>2000$ && $\le2000$ & $>2000$  && $\le2000$ & $>2000$ \\" _n
file write tablewrite "[0.5em]" _n
file write tablewrite "Mean of dep var & `ymean1' & `ymean2' && `ymean3' & `ymean4' && `ymean5' & `ymean6' \\" _n
file write tablewrite "Clusters & `nclust1' & `nclust2' && `nclust3' & `nclust4' && `nclust5' & `nclust6' \\" _n
file write tablewrite "Observations & `nobs1' & `nobs2' && `nobs3' & `nobs4' && `nobs5' & `nobs6' \\" _n
file write tablewrite "\hline" _n
file write tablewrite "\end{tabular}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\caption*{\scriptsize Note. --- District-level DD with two NSS years (2005, 2010), " _n
file write tablewrite "splitting on 2001 village population before collapsing to the district level using NSS sampling weights. " _n
file write tablewrite "Regressions are otherwise identical to those in Table \ref*{tab:nss_first_stage_no_state_trends}. " _n
file write tablewrite "We do not observe village populations in the 2000 NSS wave, meaning that in order to estimate a 3-period panel " _n
file write tablewrite "that removes extremely large villages, we can only split on the distribution of village weights. " _n
file write tablewrite "All regressions include: district fixed effects; year fixed effects; " _n
file write tablewrite "linear trends in state quartiles of 2005 household expenditures per capita; " _n 
file write tablewrite "and linear trends in national deciles of 2005 household expenditures per capita. " _n
file write tablewrite "Standard errors are clustered at the district level, collapsing to a " _n
file write tablewrite "single cluster for (i) districts that split in the 2001 Census, but which " _n
file write tablewrite "the 2000 NSS sampled based on 1991 district definitions; and (ii) the few cases " _n
file write tablewrite "where an RGGVY DPR included multiple districts." _n
file write tablewrite "Significance: *** \$p < 0.01\$, ** \$p < 0.05\$, * \$p < 0.10\$." _n
file write tablewrite "}" _n
file write tablewrite "\end{table}" _n

file close tablewrite

}

********************************************************************************
********************************************************************************

** Table A8: NSS first-stage DD, extensive and intensive (Q1)
{
cap file close tablewrite
use "$results/nss_reg_results.dta", clear
keep if panel=="district-year collapsed"
keep if regs=="ols"
keep if inlist(yvar,"elec_q_yn","log_elec_q","elec_quantity")
keep if inlist(ytag,"_dec12")
keep if ifs==""
keep if inlist(fes,"year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt", ///
	"year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt")

gen c = .
replace c = 1 if yvar=="elec_q_yn" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_dec12"
replace c = 2 if yvar=="elec_q_yn" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt" & ytag=="_dec12"	
replace c = 3 if yvar=="elec_quantity" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_dec12"
replace c = 4 if yvar=="elec_quantity" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt" & ytag=="_dec12"
replace c = 5 if yvar=="log_elec_q" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_dec12"
replace c = 6 if yvar=="log_elec_q" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt" & ytag=="_dec12"
assert c!=.	
sort c

forvalues c = 1/6 {
		
	if inlist(`c',3,4) {
	    local beta`c' = string(beta[`c'],"%9.2f")
		local se`c' = string(se[`c'],"%9.2f")
	}
	else {
	    local beta`c' = string(beta[`c'],"%9.3f")
		local se`c' = string(se[`c'],"%9.3f")	    
	}
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if  pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}

	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']
	if inlist(`c',3,4) {
	    local ymean`c' = string(ymean_pooled[`c'],"%9.2f")
	}
	else {
	    local ymean`c' = string(ymean_pooled[`c'],"%9.3f")	    
	}
}	

use "$panel/panel_dataset_dd_nss_uncollapsed.dta", clear
egen vill_tag = tag(fsu_serial st_code dt_code year)
sum frame_pop if inrange(WT_decile,1,2) & vill_tag, detail
local pop_p50_1 = string(r(p50),"%9.0f")
local pop_p90_1 = string(r(p90),"%9.0f")
sum frame_pop if inrange(WT_decile,3,10) & vill_tag, detail
local pop_p50_2 = string(r(p50),"%9.0f")
local pop_p90_2 = string(r(p90),"%9.0f")



	
   // MAKE TABLE
file open tablewrite using "$textab/table_nss_first_stage_q1.tex", write text replace
 
file write tablewrite "\begin{table}[h!]\centering" _n
file write tablewrite "\caption{District-level first stage DD -- villages in weight quintile 1}" _n
file write tablewrite "\label{tab:nss_first_stage_q1}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\small" _n
file write tablewrite "\begin{tabular}{lccccccccc}" _n
file write tablewrite "\hline" _n
file write tablewrite "& \multicolumn{2}{c}{\$ \mathbf{1}\big[\text{kWh} > 0\big] \$} & "  _n
file write tablewrite "& \multicolumn{2}{c}{\$ \text{kWh/month} \$} & " _n
file write tablewrite "& \multicolumn{2}{c}{\$ \log\big(\text{kWh/month}\big) \$} \\" _n
file write tablewrite "[0.2em]" _n
file write tablewrite "& (1) & (2) && (3) & (4) && (5) & (6) \\" _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\cline{2-3} \cline{5-6} \cline{8-9}\\" _n
file write tablewrite "\vspace{-0.80cm}" _n
file write tablewrite "\\" _n
file write tablewrite "$\mathbf{1}\big[\text{10th-Plan district}\big] \times \mathbf{1}\big[2010\big]$~~ & " _n
file write tablewrite "$`beta1'$`stars1' & $`beta2'$`stars2' && $`beta3'$`stars3' & $`beta4'$`stars4' && $`beta5'$`stars5' & $`beta6'$`stars6' \\" _n
file write tablewrite "& $(`se1')$ & $(`se2')$ && $(`se3')$ & $(`se4')$ && $(`se5')$ & $(`se6')$ \\" _n
file write tablewrite "[0.8em]" _n
file write tablewrite "State-specific linear trends  &  & Yes &&  & Yes && & Yes \\" _n
file write tablewrite "[0.5em]" _n
file write tablewrite "Mean of dep var & `ymean1' & `ymean2' && `ymean3' & `ymean4' && `ymean5' & `ymean6' \\" _n
file write tablewrite "Clusters & `nclust1' & `nclust2' && `nclust3' & `nclust4' && `nclust5' & `nclust6' \\" _n
file write tablewrite "Observations & `nobs1' & `nobs2' && `nobs3' & `nobs4' && `nobs5' & `nobs6' \\" _n
file write tablewrite "\hline" _n
file write tablewrite "\end{tabular}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\caption*{\scriptsize Note. --- Regressions are identical to those in Tables \ref*{tab:nss_first_stage} and " _n
file write tablewrite "\ref*{tab:nss_first_stage_no_state_trends}, except that we restrict the sample to villages in  " _n
file write tablewrite "the first quintile of NSS village weights before collapsing to the district level using sampling weights. " _n
file write tablewrite "We do not observe village populations for the 2000 NSS wave, meaning that we cannot estimate a 3-period panel " _n
file write tablewrite "splitting directly on village size. However, isolating the first quintile of NSS sampling weights shifts " _n
file write tablewrite "the distribution of 2001 village populations (as observed in 2005 and 2010 waves) towards smaller villages.  " _n
file write tablewrite "The 50th (90th) percentile village in weight quintile 1 had a 2001 population of `pop_p50_1' (`pop_p90_1'). " _n
file write tablewrite "All regressions include: district fixed effects; year fixed effects; " _n
file write tablewrite "linear trends in state quartiles of 2005 household expenditures per capita; " _n 
file write tablewrite "and linear trends in national deciles of 2005 household expenditures per capita. " _n
file write tablewrite "Standard errors are clustered at the district level, collapsing to a " _n
file write tablewrite "single cluster for (i) districts that split in the 2001 Census, but which " _n
file write tablewrite "the 2000 NSS sampled based on 1991 district definitions; and (ii) the few cases " _n
file write tablewrite "where an RGGVY DPR included multiple districts." _n
file write tablewrite "Significance: *** \$p < 0.01\$, ** \$p < 0.05\$, * \$p < 0.10\$." _n
file write tablewrite "}" _n
file write tablewrite "\end{table}" _n

file close tablewrite

}

********************************************************************************
********************************************************************************

** Table A9: NSS first-stage DD, extensive and intensive (Q25)
{
cap file close tablewrite
use "$results/nss_reg_results.dta", clear
keep if panel=="district-year collapsed"
keep if regs=="ols"
keep if inlist(yvar,"elec_q_yn","log_elec_q","elec_quantity")
keep if inlist(ytag,"_dec30")
keep if ifs==""
keep if inlist(fes,"year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt", ///
	"year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt")

gen c = .
replace c = 1 if yvar=="elec_q_yn" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_dec30"
replace c = 2 if yvar=="elec_q_yn" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt" & ytag=="_dec30"	
replace c = 3 if yvar=="elec_quantity" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_dec30"
replace c = 4 if yvar=="elec_quantity" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt" & ytag=="_dec30"
replace c = 5 if yvar=="log_elec_q" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_dec30"
replace c = 6 if yvar=="log_elec_q" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt" & ytag=="_dec30"
assert c!=.	
sort c

forvalues c = 1/6 {
		
	if inlist(`c',3,4) {
	    local beta`c' = string(beta[`c'],"%9.2f")
		local se`c' = string(se[`c'],"%9.2f")
	}
	else {
	    local beta`c' = string(beta[`c'],"%9.3f")
		local se`c' = string(se[`c'],"%9.3f")	    
	}
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if  pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}

	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']
	if inlist(`c',3,4) {
	    local ymean`c' = string(ymean_pooled[`c'],"%9.2f")
	}
	else {
	    local ymean`c' = string(ymean_pooled[`c'],"%9.3f")	    
	}
}	

use "$panel/panel_dataset_dd_nss_uncollapsed.dta", clear
egen vill_tag = tag(fsu_serial st_code dt_code year)
sum frame_pop if inrange(WT_decile,1,2) & vill_tag, detail
local pop_p50_1 = string(r(p50),"%9.0f")
local pop_p90_1 = string(r(p90),"%9.0f")
sum frame_pop if inrange(WT_decile,3,10) & vill_tag, detail
local pop_p50_2 = string(r(p50),"%9.0f")
local pop_p90_2 = string(r(p90),"%9.0f")



	
   // MAKE TABLE
file open tablewrite using "$textab/table_nss_first_stage_q25.tex", write text replace
 
file write tablewrite "\begin{table}[h!]\centering" _n
file write tablewrite "\caption{District-level first stage DD -- villages in weight quintiles 2--5}" _n
file write tablewrite "\label{tab:nss_first_stage_q25}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\small" _n
file write tablewrite "\begin{tabular}{lccccccccc}" _n
file write tablewrite "\hline" _n
file write tablewrite "& \multicolumn{2}{c}{\$ \mathbf{1}\big[\text{kWh} > 0\big] \$} & "  _n
file write tablewrite "& \multicolumn{2}{c}{\$ \text{kWh/month} \$} & " _n
file write tablewrite "& \multicolumn{2}{c}{\$ \log\big(\text{kWh/month}\big) \$} \\" _n
file write tablewrite "[0.2em]" _n
file write tablewrite "& (1) & (2) && (3) & (4) && (5) & (6) \\" _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\cline{2-3} \cline{5-6} \cline{8-9}\\" _n
file write tablewrite "\vspace{-0.80cm}" _n
file write tablewrite "\\" _n
file write tablewrite "$\mathbf{1}\big[\text{10th-Plan district}\big] \times \mathbf{1}\big[2010\big]$~~ & " _n
file write tablewrite "$`beta1'$`stars1' & $`beta2'$`stars2' && $`beta3'$`stars3' & $`beta4'$`stars4' && $`beta5'$`stars5' & $`beta6'$`stars6' \\" _n
file write tablewrite "& $(`se1')$ & $(`se2')$ && $(`se3')$ & $(`se4')$ && $(`se5')$ & $(`se6')$ \\" _n
file write tablewrite "[0.8em]" _n
file write tablewrite "State-specific linear trends  &  & Yes &&  & Yes && & Yes \\" _n
file write tablewrite "[0.5em]" _n
file write tablewrite "Mean of dep var & `ymean1' & `ymean2' && `ymean3' & `ymean4' && `ymean5' & `ymean6' \\" _n
file write tablewrite "Clusters & `nclust1' & `nclust2' && `nclust3' & `nclust4' && `nclust5' & `nclust6' \\" _n
file write tablewrite "Observations & `nobs1' & `nobs2' && `nobs3' & `nobs4' && `nobs5' & `nobs6' \\" _n
file write tablewrite "\hline" _n
file write tablewrite "\end{tabular}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\caption*{\scriptsize Note. --- Regressions are identical to Table \ref*{tab:nss_first_stage_q1}, " _n
file write tablewrite "except using the opposite set of NSS villages in sampling weight quintiles 2--5. " _n
file write tablewrite "The 50th (90th) percentile village in weight quintiles 2--5 had a 2001 population of `pop_p50_2' (`pop_p90_2'). " _n
file write tablewrite "See notes under Table \ref*{tab:nss_first_stage_q1} for details on fixed effects, linear trends, and standard errors." _n
file write tablewrite "Significance: *** \$p < 0.01\$, ** \$p < 0.05\$, * \$p < 0.10\$." _n
file write tablewrite "}" _n
file write tablewrite "\end{table}" _n

file close tablewrite

}

********************************************************************************
********************************************************************************

** Table A11: NSS first-stage spillover check -- value of fuels purhcased for self-gen
{
cap file close tablewrite
use "$results/nss_reg_results.dta", clear
keep if panel=="district-year collapsed"
keep if regs=="ols"
keep if inlist(yvar,"othfuel_val")
keep if inlist(ytag,"","_dec12","_dec30")
keep if ifs==""
keep if inlist(fes,"year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt", ///
	"year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt")

gen c = .
replace c = 1 if ytag=="" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt"	
replace c = 2 if ytag=="" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt"	
replace c = 3 if ytag=="_dec12" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt"	
replace c = 4 if ytag=="_dec12" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt"	
replace c = 5 if ytag=="_dec30" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt"	
replace c = 6 if ytag=="_dec30" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt"	
assert c!=.	
sort c


	// Diesel price in 2010 (Rs per L)
local p_diesel = 38.1	// https://www.mycarhelpline.com/index.php?option=com_easyblog&view=entry&id=808&Itemid=91

	// Assumed L-to-kWh conversion rate for a diesel backup generator
local l_per_kwh = 0.3 // https://www.generatorsource.com/Diesel_Fuel_Consumption.aspx
local L_per_kwh = string(`l_per_kwh',"%9.1f")	

forvalues c = 1/6 {
		
	local beta`c' = string(beta[`c'],"%9.2f")
	local se`c' = string(se[`c'],"%9.2f")
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if  pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}

	local ymean`c' = string(ymean_pooled[`c'],"%9.2f")
	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']
	
	// put LCI in terms of kWh/month
	local lci`c' = string(ci95_lo[`c'] / `p_diesel' / `l_per_kwh' , "%9.2f")
}	

	
   // MAKE TABLE
file open tablewrite using "$textab/table_nss_first_stage_selfgen_fuels.tex", write text replace
 
file write tablewrite "\begin{table}[h!]\centering" _n
file write tablewrite "\caption{District-level DD of fuel purchases for self-generation}" _n
file write tablewrite "\label{tab:nss_first_stage_selfgen_fuels}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\small " _n
file write tablewrite "\begin{tabular}{lccccccccccc}" _n
file write tablewrite "\hline" _n
file write tablewrite "& \multicolumn{8}{c}{Diesel/petrol purchases per household (Rs/month)}  \\ " _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\cline{2-9}\\" _n
file write tablewrite "\vspace{-0.90cm}" _n
file write tablewrite "\\" _n
file write tablewrite "& \multicolumn{2}{c}{Pooled} " _n
file write tablewrite "&& \multicolumn{2}{c}{Quintile 1} " _n
file write tablewrite "&& \multicolumn{2}{c}{Quintiles 2--5}" _n
file write tablewrite " \\" _n
file write tablewrite "& (1) & (2)  && (3) & (4) && (5) & (6) \\" _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\cline{2-3} \cline{5-6} \cline{8-9}" _n
file write tablewrite "\vspace{-0.20cm}" _n
file write tablewrite "\\" _n
file write tablewrite "$\mathbf{1}\big[\text{10th-Plan}\big] \times \mathbf{1}\big[2010\big]$ & " _n
file write tablewrite "$`beta1'$`stars1' & $`beta2'$`stars2' && " _n
file write tablewrite "$`beta3'$`stars3' & $`beta4'$`stars4' && " _n
file write tablewrite "$`beta5'$`stars5' & $`beta6'$`stars6' \\ " _n
file write tablewrite "& $(`se1')$ & $(`se2')$ && $(`se3')$ & $(`se4')$ && $(`se5')$ & $(`se6')$ \\" _n
file write tablewrite "[0.5em]" _n
file write tablewrite "Crowding out we can reject (kWh/month) & $`lci1'$ & $`lci2'$ && $`lci3'$ & $`lci4'$ && $`lci5'$ & $`lci6'$ \\" _n
file write tablewrite "[0.5em]" _n
file write tablewrite "State-specific linear trends & & Yes && & Yes && & Yes \\"
file write tablewrite "[0.5em]" _n
file write tablewrite "Mean of dep var (Rs/month) & `ymean1' & `ymean2' && `ymean3' & `ymean4' && `ymean5' & `ymean6' \\" _n
file write tablewrite "Clusters & `nclust1' & `nclust2' && `nclust3' & `nclust4' && `nclust5' & `nclust6'  \\" _n
file write tablewrite "Observations & `nobs1' & `nobs2' && `nobs3' & `nobs4' && `nobs5' & `nobs6' \\" _n
file write tablewrite "\hline" _n
file write tablewrite "\end{tabular}" _n
file write tablewrite "\vspace{-3mm}" _n
file write tablewrite "\caption*{\scriptsize Note. --- Regressions are identical to Tables \ref*{tab:nss_first_stage} " _n
file write tablewrite "and \ref{tab:nss_first_stage_no_state_trends}, except that Columns (3)--(6) split by " _n
file write tablewrite "quintile of NSS sampling weights before collapsing to a district-year panel. "
file write tablewrite "The outcome variable is the total value of diesel and petrol purchased for self-generation " _n
file write tablewrite "of electricity, at the household-month level. " _n
file write tablewrite "The second row converts the lower bound of each 95\% confidence interval from Rs/month to kWh/month,  " _n
file write tablewrite "assuming a 2010 diesel price of `p_diesel' Rs/L and a diesel generator that uses `L_per_kwh' L to produce 1 kWh. " _n
file write tablewrite "All regressions include: district fixed effects; year fixed effects;  " _n
file write tablewrite "linear trends in state quartiles of 2005 household expenditures per capita; " _n 
file write tablewrite "and linear trends in national deciles of 2005 household expenditures per capita. " _n
file write tablewrite "Standard errors are clustered at the district level, collapsing to a " _n
file write tablewrite "single cluster for (i) districts that split in the 2001 Census, but which " _n
file write tablewrite "the 2000 NSS sampled based on 1991 district definitions; and (ii) the few cases " _n
file write tablewrite "where an RGGVY DPR included multiple districts." _n
file write tablewrite "Significance: *** \$p < 0.01\$, ** \$p < 0.05\$, * \$p < 0.10\$." _n
file write tablewrite "}" _n
file write tablewrite "\end{table}" _n

file close tablewrite

}

********************************************************************************
********************************************************************************

** Table A14: NSS first-stage DD, heterogeneous by RGGVY implementation intensity
{
cap file close tablewrite
use "$results/nss_reg_results.dta", clear
keep if panel=="district-year collapsed"
keep if regs=="ols (DPR interaction)"
keep if inlist(yvar,"elec_q_yn","elec_quantity")
keep if inlist(ytag,"","_dec12","_dec30")
keep if ifs==""
keep if inlist(fes,"year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt")

gen c = .
replace c = 1 if yvar=="elec_q_yn" & ytag==""
replace c = 2 if yvar=="elec_q_yn" & ytag=="_dec12"
replace c = 3 if yvar=="elec_q_yn" & ytag=="_dec30"
replace c = 4 if yvar=="elec_quantity" & ytag==""
replace c = 5 if yvar=="elec_quantity" & ytag=="_dec12"
replace c = 6 if yvar=="elec_quantity" & ytag=="_dec30"
assert c!=.	
sort c
	
foreach c in 1 2 3 {

	local beta_hi`c' = string(beta_dpr_hi[`c'],"%9.3f")
	local se_hi`c' = string(se_dpr_hi[`c'],"%9.3f")
	if pvalue_dpr_hi[`c'] <= 0.01 {
		local stars_hi`c' = "$^{***}$"
	}
	else if pvalue_dpr_hi[`c'] <= 0.05 {
		local stars_hi`c' = "$^{**}$"
	}
	else if pvalue_dpr_hi[`c'] <= 0.10 {
		local stars_hi`c' = "$^{*}$"
	}
	else {
		local stars_hi`c' = ""
	}
	
    local beta_lo`c' = string(beta_dpr_lo[`c'],"%9.3f")
	local se_lo`c' = string(se_dpr_lo[`c'],"%9.3f")
	if pvalue_dpr_lo[`c'] <= 0.01 {
		local stars_lo`c' = "$^{***}$"
	}
	else if pvalue_dpr_lo[`c'] <= 0.05 {
		local stars_lo`c' = "$^{**}$"
	}
	else if pvalue_dpr_lo[`c'] <= 0.10 {
		local stars_lo`c' = "$^{*}$"
	}
	else {
		local stars_lo`c' = ""
	}

	local lci_hi`c' = string(ci95_lo_dpr_hi[`c'],"%9.3f")
	local uci_hi`c' = string(ci95_hi_dpr_hi[`c'],"%9.3f")
	local lci_lo`c' = string(ci95_lo_dpr_lo[`c'],"%9.3f")
	local uci_lo`c' = string(ci95_hi_dpr_lo[`c'],"%9.3f")

	local ymean`c' = string(ymean_pooled[`c'],"%9.3f")
	local ymean_hi`c' = string(ymean_dpr_hi[`c'],"%9.3f")
	local ymean_lo`c' = string(ymean_dpr_lo[`c'],"%9.3f")	    

	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']

	local pval_equal`c' = string(pval_equal[`c'],"%9.3f")
}

foreach c in 4 5 6 {

	local beta_hi`c' = string(beta_dpr_hi[`c'],"%9.2f")
	local se_hi`c' = string(se_dpr_hi[`c'],"%9.2f")
	if pvalue_dpr_hi[`c'] <= 0.01 {
		local stars_hi`c' = "$^{***}$"
	}
	else if pvalue_dpr_hi[`c'] <= 0.05 {
		local stars_hi`c' = "$^{**}$"
	}
	else if pvalue_dpr_hi[`c'] <= 0.10 {
		local stars_hi`c' = "$^{*}$"
	}
	else {
		local stars_hi`c' = ""
	}
	
    local beta_lo`c' = string(beta_dpr_lo[`c'],"%9.2f")
	local se_lo`c' = string(se_dpr_lo[`c'],"%9.2f")
	if pvalue_dpr_lo[`c'] <= 0.01 {
		local stars_lo`c' = "$^{***}$"
	}
	else if pvalue_dpr_lo[`c'] <= 0.05 {
		local stars_lo`c' = "$^{**}$"
	}
	else if pvalue_dpr_lo[`c'] <= 0.10 {
		local stars_lo`c' = "$^{*}$"
	}
	else {
		local stars_lo`c' = ""
	}

	local lci_hi`c' = string(ci95_lo_dpr_hi[`c'],"%9.2f")
	local uci_hi`c' = string(ci95_hi_dpr_hi[`c'],"%9.2f")
	local lci_lo`c' = string(ci95_lo_dpr_lo[`c'],"%9.2f")
	local uci_lo`c' = string(ci95_hi_dpr_lo[`c'],"%9.2f")

	local ymean`c' = string(ymean_pooled[`c'],"%9.2f")
	local ymean_hi`c' = string(ymean_dpr_hi[`c'],"%9.2f")
	local ymean_lo`c' = string(ymean_dpr_lo[`c'],"%9.2f")

	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']

	local pval_equal`c' = string(pval_equal[`c'],"%9.3f")
}



   // MAKE TABLE
file open tablewrite using "$textab/table_nss_fs_intens.tex", write text replace
 
file write tablewrite "\begin{table}[h!]\centering" _n
file write tablewrite "\caption{District-level DD -- first stage, high- vs.\ low-intensity districts}" _n
file write tablewrite "\label{tab:nss_fs_intens}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\small" _n
file write tablewrite "\begin{tabular}{lccccccccccc}" _n
file write tablewrite "\hline" _n
file write tablewrite "& \multicolumn{3}{c}{\$ \mathbf{1}\big[\text{kWh} > 0\big] \$} & "  _n
file write tablewrite "& \multicolumn{3}{c}{\$ \text{kWh/month} \$} \\ " _n
file write tablewrite "[0.2em]" _n
file write tablewrite "& (1) & (2) & (3) && (4) & (5) & (6) \\" _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\cline{2-4} \cline{6-8}\\" _n
file write tablewrite "\vspace{-0.80cm}" _n
file write tablewrite "\\" _n
file write tablewrite "$\mathbf{1}\big[\text{10th-Plan district}\big] \times \mathbf{1}\big[2010\big] \, \times\$ \\ " _n
file write tablewrite "[0.3em]" _n
file write tablewrite "~~~\$>60\$\% of villages treated & " _n
file write tablewrite "$`beta_hi1'$`stars_hi1' & $`beta_hi2'$`stars_hi2' & $`beta_hi3'$`stars_hi3' && " _n
file write tablewrite "$`beta_hi4'$`stars_hi4' & $`beta_hi5'$`stars_hi5' & $`beta_hi6'$`stars_hi6' \\ " _n
file write tablewrite "& $(`se_hi1')$ & $(`se_hi2')$ & $(`se_hi3')$ && $(`se_hi4')$ & $(`se_hi5')$ & $(`se_hi6')$ \\" _n
file write tablewrite "[0.8em]" _n
file write tablewrite "~~~\$<60\$\% of villages treated & " _n
file write tablewrite "$`beta_lo1'$`stars_lo1' & $`beta_lo2'$`stars_lo2' & $`beta_lo3'$`stars_lo3' && " _n
file write tablewrite "$`beta_lo4'$`stars_lo4' & $`beta_lo5'$`stars_lo5' & $`beta_lo6'$`stars_lo6' \\ " _n
file write tablewrite "& $(`se_lo1')$ & $(`se_lo2')$ & $(`se_lo3')$ && $(`se_lo4')$ & $(`se_lo5')$ & $(`se_lo6')$ \\" _n
file write tablewrite "[0.8em]" _n
file write tablewrite "\$p\$-value on test of equality & " _n
file write tablewrite "`pval_equal1' & `pval_equal2' & `pval_equal3' && `pval_equal4' & `pval_equal5' & `pval_equal6' \\" _n
file write tablewrite "[0.8em]" _n
file write tablewrite "Village weight quintiles & Pooled & 1 & 2--5 && Pooled & 1 & 2--5 \\" _n
file write tablewrite "[0.8em]" _n
file write tablewrite "Mean of dep var, \$>60\$\% treated & " _n
file write tablewrite "~~`ymean_hi1'~~ & ~~`ymean_hi2'~~ & ~~`ymean_hi3'~~ && " _n
file write tablewrite "~~`ymean_hi4'~~ & ~~`ymean_hi5'~~ & ~~`ymean_hi6'~~ \\ " _n
file write tablewrite "Mean of dep var, \$<60\$\% treated~~~ & " _n
file write tablewrite "~~`ymean_lo1'~~ & ~~`ymean_lo2'~~ & ~~`ymean_lo3'~~ && " _n
file write tablewrite "~~`ymean_lo4'~~ & ~~`ymean_lo5'~~ & ~~`ymean_lo6'~~ \\ " _n
file write tablewrite "[0.5em]" _n
file write tablewrite "Clusters & `nclust1' & `nclust2' & `nclust3' && `nclust4' & `nclust5' & `nclust6' \\" _n
file write tablewrite "Observartions & `nobs1' & `nobs2' & `nobs3' && `nobs4' & `nobs5' & `nobs6' \\" _n
file write tablewrite "\hline" _n
file write tablewrite "\end{tabular}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\caption*{\scriptsize Note. --- We interact the DD treatment variable with indicators for " _n
file write tablewrite "10th-Plan districts where RGGVY treated more/less than 60\% of villages. " _n
file write tablewrite "Regressions split on village weight quintiles, as in Table \ref*{tab:nss_2sls}. " _n
file write tablewrite "The third row reports \$p\$-values for a test of equality of the two interacted DD coefficients. " _n
file write tablewrite "All regressions include: district fixed effects; year fixed effects; " _n
file write tablewrite "linear trends in state quartiles of 2005 household expenditures per capita; " _n 
file write tablewrite "and linear trends in national deciles of 2005 household expenditures per capita. " _n
file write tablewrite "Standard errors are clustered at the district level, collapsing to a " _n
file write tablewrite "single cluster for (i) districts that split in the 2001 Census, but which " _n
file write tablewrite "the 2000 NSS sampled based on 1991 district definitions; and (ii) the few cases " _n
file write tablewrite "where an RGGVY DPR included multiple districts." _n
file write tablewrite "Significance: *** \$p < 0.01\$, ** \$p < 0.05\$, * \$p < 0.10\$." _n
file write tablewrite "}" _n
file write tablewrite "\end{table}" _n

file close tablewrite

}

********************************************************************************
********************************************************************************

** Table A17: NSS reduced-form DD, heterogeneous by RGGVY implementation intensity
{
cap file close tablewrite
use "$results/nss_reg_results.dta", clear
keep if panel=="district-year collapsed"
keep if regs=="ols (DPR interaction)"
keep if inlist(yvar,"mth_pc_expE1","log_exp_30E1")
keep if inlist(ytag,"","_dec12","_dec30")
keep if ifs==""
keep if inlist(fes,"year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt")

gen c = .
replace c = 1 if yvar=="mth_pc_expE1" & ytag==""
replace c = 2 if yvar=="mth_pc_expE1" & ytag=="_dec12"
replace c = 3 if yvar=="mth_pc_expE1" & ytag=="_dec30"
replace c = 4 if yvar=="log_exp_30E1" & ytag==""
replace c = 5 if yvar=="log_exp_30E1" & ytag=="_dec12"
replace c = 6 if yvar=="log_exp_30E1" & ytag=="_dec30"
assert c!=.	
sort c

foreach c in 1 2 3 {

	local beta_hi`c' = string(beta_dpr_hi[`c'],"%9.2f")
	local se_hi`c' = string(se_dpr_hi[`c'],"%9.2f")
	if pvalue_dpr_hi[`c'] <= 0.01 {
		local stars_hi`c' = "$^{***}$"
	}
	else if pvalue_dpr_hi[`c'] <= 0.05 {
		local stars_hi`c' = "$^{**}$"
	}
	else if pvalue_dpr_hi[`c'] <= 0.10 {
		local stars_hi`c' = "$^{*}$"
	}
	else {
		local stars_hi`c' = ""
	}
	
	local beta_lo`c' = string(beta_dpr_lo[`c'],"%9.2f")
	local se_lo`c' = string(se_dpr_lo[`c'],"%9.2f")
	if pvalue_dpr_lo[`c'] <= 0.01 {
		local stars_lo`c' = "$^{***}$"
	}
	else if pvalue_dpr_lo[`c'] <= 0.05 {
		local stars_lo`c' = "$^{**}$"
	}
	else if pvalue_dpr_lo[`c'] <= 0.10 {
		local stars_lo`c' = "$^{*}$"
	}
	else {
		local stars_lo`c' = ""
	}

	local lci_hi`c' = string(ci95_lo_dpr_hi[`c'],"%9.2f")
	local uci_hi`c' = string(ci95_hi_dpr_hi[`c'],"%9.2f")
	local lci_lo`c' = string(ci95_lo_dpr_lo[`c'],"%9.2f")
	local uci_lo`c' = string(ci95_hi_dpr_lo[`c'],"%9.2f")

	local ymean`c' = string(ymean_pooled[`c'],"%9.2f")
	local ymean_hi`c' = string(ymean_dpr_hi[`c'],"%9.2f")
	local ymean_lo`c' = string(ymean_dpr_lo[`c'],"%9.2f")

	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']

	local pval_equal`c' = string(pval_equal[`c'],"%9.3f")
}

foreach c in 4 5 6 {

	local beta_hi`c' = string(beta_dpr_hi[`c'],"%9.3f")
	local se_hi`c' = string(se_dpr_hi[`c'],"%9.3f")
	if pvalue_dpr_hi[`c'] <= 0.01 {
		local stars_hi`c' = "$^{***}$"
	}
	else if pvalue_dpr_hi[`c'] <= 0.05 {
		local stars_hi`c' = "$^{**}$"
	}
	else if pvalue_dpr_hi[`c'] <= 0.10 {
		local stars_hi`c' = "$^{*}$"
	}
	else {
		local stars_hi`c' = ""
	}
	
	local beta_lo`c' = string(beta_dpr_lo[`c'],"%9.3f")
	local se_lo`c' = string(se_dpr_lo[`c'],"%9.3f")
	if pvalue_dpr_lo[`c'] <= 0.01 {
		local stars_lo`c' = "$^{***}$"
	}
	else if pvalue_dpr_lo[`c'] <= 0.05 {
		local stars_lo`c' = "$^{**}$"
	}
	else if pvalue_dpr_lo[`c'] <= 0.10 {
		local stars_lo`c' = "$^{*}$"
	}
	else {
		local stars_lo`c' = ""
	}

	local lci_hi`c' = string(ci95_lo_dpr_hi[`c'],"%9.3f")
	local uci_hi`c' = string(ci95_hi_dpr_hi[`c'],"%9.3f")
	local lci_lo`c' = string(ci95_lo_dpr_lo[`c'],"%9.3f")
	local uci_lo`c' = string(ci95_hi_dpr_lo[`c'],"%9.3f")

	local ymean`c' = string(ymean_pooled[`c'],"%9.3f")
	local ymean_hi`c' = string(ymean_dpr_hi[`c'],"%9.3f")
	local ymean_lo`c' = string(ymean_dpr_lo[`c'],"%9.3f")

	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']

	local pval_equal`c' = string(pval_equal[`c'],"%9.3f")
}


   // MAKE TABLE
file open tablewrite using "$textab/table_nss_rf_intens.tex", write text replace
 
file write tablewrite "\begin{table}[h!]\centering" _n
file write tablewrite "\caption{District-level DD -- reduced form, high- vs.\ low-intensity districts}" _n
file write tablewrite "\label{tab:nss_rf_intens}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\small" _n
file write tablewrite "\begin{tabular}{lccccccccc}" _n
file write tablewrite "\hline" _n
file write tablewrite "& \multicolumn{7}{c}{Expenditure per capita (Rs/month)}  \\ " _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\cline{2-8}\\" _n
file write tablewrite "\vspace{-0.90cm}" _n
file write tablewrite "\\" _n
file write tablewrite "& \multicolumn{3}{c}{Levels} & " _n
file write tablewrite "& \multicolumn{3}{c}{Logs} \\" _n
file write tablewrite "& (1) & (2) & (3) && (4) & (5) & (6) \\" _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\cline{2-4} \cline{6-8}" _n
file write tablewrite "\vspace{-0.20cm}" _n
file write tablewrite "\\" _n
file write tablewrite "$\mathbf{1}\big[\text{10th-Plan district}\big] \times \mathbf{1}\big[2010\big] \, \times\$ \\ " _n
file write tablewrite "[0.3em]" _n
file write tablewrite "~~~\$>60\$\% of villages treated & " _n
file write tablewrite "$`beta_hi1'$`stars_hi1' & $`beta_hi2'$`stars_hi2' & $`beta_hi3'$`stars_hi3' && $`beta_hi4'$`stars_hi4' & $`beta_hi5'$`stars_hi5' & $`beta_hi6'$`stars_hi6' \\" _n
file write tablewrite "& $(`se_hi1')$ & $(`se_hi2')$ & $(`se_hi3')$ && $(`se_hi4')$ & $(`se_hi5')$ & $(`se_hi6')$  \\" _n
file write tablewrite "[0.8em]" _n
file write tablewrite "~~~\$<60\$\% of villages treated & " _n
file write tablewrite "$`beta_lo1'$`stars_lo1' & $`beta_lo2'$`stars_lo2' & $`beta_lo3'$`stars_lo3' && $`beta_lo4'$`stars_lo4' & $`beta_lo5'$`stars_lo5' & $`beta_lo6'$`stars_lo6' \\" _n
file write tablewrite "& $(`se_lo1')$ & $(`se_lo2')$ & $(`se_lo3')$ && $(`se_lo4')$ & $(`se_lo5')$ & $(`se_lo6')$ \\" _n
file write tablewrite "[0.8em]" _n
file write tablewrite "\$p\$-value on test of equality & " _n
file write tablewrite "`pval_equal1' & `pval_equal2' & `pval_equal3' && `pval_equal4' & `pval_equal5' & `pval_equal6' \\" _n
file write tablewrite "[0.8em]" _n
file write tablewrite "Village weight quintiles & Pooled & 1 & 2--5 && Pooled & 1 & 2--5 \\" _n
file write tablewrite "[0.8em]" _n
file write tablewrite "Mean of dep var, \$>60\$\% treated~~ & `ymean_hi1' & `ymean_hi2' & `ymean_hi3' && `ymean_hi4' & `ymean_hi5' & `ymean_hi6' \\" _n
file write tablewrite "Mean of dep var, \$<60\$\% treated~~ & `ymean_lo1' & `ymean_lo2' & `ymean_lo3' && `ymean_lo4' & `ymean_lo5' & `ymean_lo6' \\" _n
file write tablewrite "[0.5em]" _n
file write tablewrite "Clusters & `nclust1' & `nclust2' & `nclust3' && `nclust4' & `nclust5' & `nclust6' \\" _n
file write tablewrite "Observations & `nobs1' & `nobs2' & `nobs3' && `nobs4' & `nobs5' & `nobs6' \\" _n
file write tablewrite "\hline" _n
file write tablewrite "\end{tabular}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\caption*{\scriptsize Note. --- Regressions are identical to those in Table \ref{tab:nss_fs_intens}, " _n
file write tablewrite "except that they use monthly expenditure per capita as the outcome variable. " _n
file write tablewrite "The third row reports \$p\$-values for a test of equality of the two interacted DD coefficients. " _n
file write tablewrite "All regressions include: district fixed effects; year fixed effects; " _n
file write tablewrite "linear trends in state quartiles of 2005 household expenditures per capita; " _n 
file write tablewrite "and linear trends in national deciles of 2005 household expenditures per capita. " _n
file write tablewrite "Standard errors are clustered at the district level, collapsing to a " _n
file write tablewrite "single cluster for (i) districts that split in the 2001 Census, but which " _n
file write tablewrite "the 2000 NSS sampled based on 1991 district definitions; and (ii) the few cases " _n
file write tablewrite "where an RGGVY DPR included multiple districts." _n
file write tablewrite "Significance: *** \$p < 0.01\$, ** \$p < 0.05\$, * \$p < 0.10\$." _n
file write tablewrite "}" _n
file write tablewrite "\end{table}" _n

file close tablewrite

}

********************************************************************************
********************************************************************************

** Table A20: NSS first-stage DD, heterogeneous by hours/day of power to rural households
{
cap file close tablewrite
use "$results/nss_reg_results.dta", clear
keep if panel=="district-year collapsed"
keep if regs=="ols (HRS interaction)"
keep if inlist(yvar,"elec_q_yn","elec_quantity") //,"log_elec_q","mth_pc_expE1","log_exp_30E1")
keep if inlist(ytag,"","_dec12","_dec30")
keep if ifs==""
keep if inlist(fes,"year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt")

gen c = .
replace c = 1 if yvar=="elec_q_yn" & ytag==""
replace c = 2 if yvar=="elec_quantity" & ytag==""
replace c = 3 if yvar=="elec_q_yn" & ytag=="_dec12"
replace c = 4 if yvar=="elec_quantity" & ytag=="_dec12"
replace c = 5 if yvar=="elec_q_yn" & ytag=="_dec30"
replace c = 6 if yvar=="elec_quantity" & ytag=="_dec30"
assert c!=.	
sort c

foreach c in 1 3 5 {

	local beta_hi`c' = string(beta_hrs_hi[`c'],"%9.3f")
	local se_hi`c' = string(se_hrs_hi[`c'],"%9.3f")
	if pvalue_hrs_hi[`c'] <= 0.01 {
		local stars_hi`c' = "$^{***}$"
	}
	else if pvalue_hrs_hi[`c'] <= 0.05 {
		local stars_hi`c' = "$^{**}$"
	}
	else if pvalue_hrs_hi[`c'] <= 0.10 {
		local stars_hi`c' = "$^{*}$"
	}
	else {
		local stars_hi`c' = ""
	}
	
	local beta_lo`c' = string(beta_hrs_lo[`c'],"%9.3f")
	local se_lo`c' = string(se_hrs_lo[`c'],"%9.3f")
	if pvalue_hrs_lo[`c'] <= 0.01 {
		local stars_lo`c' = "$^{***}$"
	}
	else if pvalue_hrs_lo[`c'] <= 0.05 {
		local stars_lo`c' = "$^{**}$"
	}
	else if pvalue_hrs_lo[`c'] <= 0.10 {
		local stars_lo`c' = "$^{*}$"
	}
	else {
		local stars_lo`c' = ""
	}

	local lci_hi`c' = string(ci95_lo_hrs_hi[`c'],"%9.3f")
	local uci_hi`c' = string(ci95_hi_hrs_hi[`c'],"%9.3f")
	local lci_lo`c' = string(ci95_lo_hrs_lo[`c'],"%9.3f")
	local uci_lo`c' = string(ci95_hi_hrs_lo[`c'],"%9.3f")

	local ymean`c' = string(ymean_pooled[`c'],"%9.3f")
	local ymean_hi`c' = string(ymean_hrs_hi[`c'],"%9.3f")
	local ymean_lo`c' = string(ymean_hrs_lo[`c'],"%9.3f")

	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']

	local pval_equal`c' = string(pval_equal[`c'],"%9.3f")
}

foreach c in 2 4 6 {

	local beta_hi`c' = string(beta_hrs_hi[`c'],"%9.2f")
	local se_hi`c' = string(se_hrs_hi[`c'],"%9.2f")
	if pvalue_hrs_hi[`c'] <= 0.01 {
		local stars_hi`c' = "$^{***}$"
	}
	else if pvalue_hrs_hi[`c'] <= 0.05 {
		local stars_hi`c' = "$^{**}$"
	}
	else if pvalue_hrs_hi[`c'] <= 0.10 {
		local stars_hi`c' = "$^{*}$"
	}
	else {
		local stars_hi`c' = ""
	}
	
	local beta_lo`c' = string(beta_hrs_lo[`c'],"%9.2f")
	local se_lo`c' = string(se_hrs_lo[`c'],"%9.2f")
	if pvalue_hrs_lo[`c'] <= 0.01 {
		local stars_lo`c' = "$^{***}$"
	}
	else if pvalue_hrs_lo[`c'] <= 0.05 {
		local stars_lo`c' = "$^{**}$"
	}
	else if pvalue_hrs_lo[`c'] <= 0.10 {
		local stars_lo`c' = "$^{*}$"
	}
	else {
		local stars_lo`c' = ""
	}

	local lci_hi`c' = string(ci95_lo_hrs_hi[`c'],"%9.2f")
	local uci_hi`c' = string(ci95_hi_hrs_hi[`c'],"%9.2f")
	local lci_lo`c' = string(ci95_lo_hrs_lo[`c'],"%9.2f")
	local uci_lo`c' = string(ci95_hi_hrs_lo[`c'],"%9.2f")

	local ymean`c' = string(ymean_pooled[`c'],"%9.2f")
	local ymean_hi`c' = string(ymean_hrs_hi[`c'],"%9.2f")
	local ymean_lo`c' = string(ymean_hrs_lo[`c'],"%9.2f")

	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']

	local pval_equal`c' = string(pval_equal[`c'],"%9.3f")
}


   // MAKE TABLE
file open tablewrite using "$textab/table_nss_fs_hours.tex", write text replace
 
file write tablewrite "\begin{table}[h!]\centering" _n
file write tablewrite "\caption{District-level DD -- first stage, heterogeneous effects in districts' power supply}" _n
file write tablewrite "\label{tab:nss_fs_hours}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\small" _n
file write tablewrite "\begin{tabular}{lccccccccc}" _n
file write tablewrite "\hline" _n
file write tablewrite "& \multicolumn{8}{c}{HH electricity use (kWh/month)} \\ " _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\cline{2-9}\\" _n
file write tablewrite "\vspace{-0.90cm}" _n
file write tablewrite "\\" _n
file write tablewrite "& \$\mathbf{1}\big[Q>0\big]\$ & Levels && \$\mathbf{1}\big[Q>0\big]\$ & Levels && \$\mathbf{1}\big[Q>0\big]\$ & Levels \\" _n
file write tablewrite "& (1) & (2) && (3) & (4) && (5) & (6) \\" _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\hline" _n
file write tablewrite "\vspace{-0.20cm}" _n
file write tablewrite "\\" _n
file write tablewrite "$\mathbf{1}\big[\text{10th-Plan district}\big] \times \mathbf{1}\big[2010\big] \, \times\$ \\ " _n
file write tablewrite "[0.3em]" _n
file write tablewrite "~~~\$\ge 10\$ hours/day of power & " _n
file write tablewrite "$`beta_hi1'$`stars_hi1' & $`beta_hi2'$`stars_hi2' && $`beta_hi3'$`stars_hi3' & $`beta_hi4'$`stars_hi4' && $`beta_hi5'$`stars_hi5' & $`beta_hi6'$`stars_hi6' \\" _n
file write tablewrite "& $(`se_hi1')$ & $(`se_hi2')$ && $(`se_hi3')$ & $(`se_hi4')$ && $(`se_hi5')$ & $(`se_hi6')$ \\" _n
file write tablewrite "[0.6em]" _n
file write tablewrite "~~~\$<10\$ hours/day of power & " _n
file write tablewrite "$`beta_lo1'$`stars_lo1' & $`beta_lo2'$`stars_lo2' && $`beta_lo3'$`stars_lo3' & $`beta_lo4'$`stars_lo4' && $`beta_lo5'$`stars_lo5' & $`beta_lo6'$`stars_lo6' \\" _n
file write tablewrite "& $(`se_lo1')$ & $(`se_lo2')$ && $(`se_lo3')$ & $(`se_lo4')$ && $(`se_lo5')$ & $(`se_lo6')$ \\" _n
file write tablewrite "[0.6em]" _n
file write tablewrite "\$p\$-value on test of equality & " _n
file write tablewrite "`pval_equal1' & `pval_equal2' && `pval_equal3' & `pval_equal4' && `pval_equal5' & `pval_equal6' \\" _n
file write tablewrite "[0.6em]" _n
file write tablewrite "Village weight quintiles & Pooled & Pooled && 1 & 1 && 2--5 & 2--5 \\" _n
file write tablewrite "[0.8em]" _n
file write tablewrite "Mean of dep var, \$\ge 10\$ hrs/day & `ymean_hi1' & `ymean_hi2' && `ymean_hi3' & `ymean_hi4' && `ymean_hi5' & `ymean_hi6'  \\" _n
file write tablewrite "Mean of dep var, \$< 10\$ hrs/day & `ymean_lo1' & `ymean_lo2' && `ymean_lo3' & `ymean_lo4' && `ymean_lo5' & `ymean_lo6'  \\" _n
file write tablewrite "[0.5em]" _n
file write tablewrite "Clusters & `nclust1' & `nclust2' && `nclust3' & `nclust4' && `nclust5' & `nclust6' \\" _n
file write tablewrite "Observations & `nobs1' & `nobs2' && `nobs3' & `nobs4' && `nobs5' & `nclust6' \\" _n
file write tablewrite "\hline" _n
file write tablewrite "\end{tabular}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\caption*{\scriptsize Note. --- We interact the DD treatment variable with indicators for " _n
file write tablewrite "rural households in the district receiving over/under 10 hours per day of power supply. " _n
file write tablewrite "We calculate this variable by averaging hours of domestic power (from the 2011 Census, at the village level) " _n
file write tablewrite "over all electrified villages in each district. " _n
file write tablewrite "The third row reports \$p\$-values for a test of equality of the two interacted DD coefficients. " _n
file write tablewrite "Regressions are otherwise identical to Columns (1)--(2) of Table \ref*{tab:nss_first_stage}, and  " _n
file write tablewrite "Columns (2) and (4) of Tables \ref{tab:nss_first_stage_q1}--\ref{tab:nss_first_stage_q25}. " _n
file write tablewrite "All regressions include: district fixed effects; year fixed effects; state-specific linear trends; " _n
file write tablewrite "linear trends in state quartiles of 2005 household expenditures per capita; " _n 
file write tablewrite "and linear trends in national deciles of 2005 household expenditures per capita. " _n
file write tablewrite "Standard errors are clustered at the district level, collapsing to a " _n
file write tablewrite "single cluster for (i) districts that split in the 2001 Census, but which " _n
file write tablewrite "the 2000 NSS sampled based on 1991 district definitions; and (ii) the few cases " _n
file write tablewrite "where an RGGVY DPR included multiple districts." _n
file write tablewrite "Significance: *** \$p < 0.01\$, ** \$p < 0.05\$, * \$p < 0.10\$." _n
file write tablewrite "}" _n
file write tablewrite "\end{table}" _n

file close tablewrite

}

********************************************************************************
********************************************************************************

** Table A21: NSS 2SLS DD, levels and logs, subset of districts with >10 hours/day of power to rural households
{
cap file close tablewrite
use "$results/nss_reg_results.dta", clear
keep if panel=="district-year collapsed"
keep if (regs=="iv (HRS splits)" & inlist(yvar,"mth_pc_expE1","log_exp_30E1")) | (regs=="ols (HRS splits)" & inlist(yvar,"elec_q_yn"))
keep if inlist(ytag,"","_dec12","_dec30")
keep if ifs==" if HRS==1"
keep if inlist(fes,"year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt")

gen c = .
replace c = 1 if yvar=="mth_pc_expE1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag==""
replace c = 2 if yvar=="mth_pc_expE1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_dec12"
replace c = 3 if yvar=="mth_pc_expE1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_dec30"
replace c = 4 if yvar=="log_exp_30E1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag==""
replace c = 5 if yvar=="log_exp_30E1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_dec12"
replace c = 6 if yvar=="log_exp_30E1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_dec30"
replace c = 7 if yvar=="elec_q_yn" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag==""
replace c = 8 if yvar=="elec_q_yn" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_dec12"
replace c = 9 if yvar=="elec_q_yn" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_dec30"
assert c!=.	
sort c

forvalues c = 1/3 {
		
	local beta`c' = string(beta[`c'],"%9.1f")
	local se`c' = string(se[`c'],"%9.1f")
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if  pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}
	
	local lci`c' = string(ci95_lo[`c'],"%9.1f")
	local uci`c' = string(ci95_hi[`c'],"%9.1f")
	local ymean`c' = string(ymean_pooled[`c'],"%9.1f")

	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']
	local fstat`c' = string(fstat[`c'],"%9.2f")
}	
	
forvalues c = 4/6 {

	local beta`c' = string(beta[`c'],"%9.3f")
	local se`c' = string(se[`c'],"%9.3f")
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if  pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}

	local lci`c' = string(ci95_lo[`c'],"%9.3f")
	local uci`c' = string(ci95_hi[`c'],"%9.3f")
	local ymean`c' = string(ymean_pooled[`c'],"%9.3f")

	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']
	local fstat`c' = string(fstat[`c'],"%9.2f")
}

forvalues c = 7/9 {

	local beta`c' = string(beta[`c'],"%9.3f")
	local se`c' = string(se[`c'],"%9.3f")
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if  pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}
}


use "$panel/panel_dataset_full.dta", clear
	// Summarize hours of power to electrified villages, by district
egen temp1 = mean(vdp_pwr_h_all_avg) if vdp_pwr_h_all_avg_11>0, by(st_code dt_code)
egen HRS_all_wide = mode(temp1), by(st_code dt_code)
egen temp2 = mean(vdp_pwr_h_dom_avg) if vdp_pwr_h_dom_avg_11>0, by(st_code dt_code)
egen HRS_dom_wide = mode(temp2), by(st_code dt_code)
gen HRS = (HRS_dom_wide>=10) & (HRS_dom_wide!=.)
keep st_code dt_code HRS
duplicates drop
merge 1:m st_code dt_code using "$panel/panel_dataset_dd_nss_uncollapsed.dta"
egen vill_tag = tag(fsu_serial st_code dt_code year)
keep if HRS==1
sum frame_pop if vill_tag, detail
local pop_p50_0 = string(r(p50),"%9.0f")
local pop_p90_0 = string(r(p90),"%9.0f")
sum frame_pop if inrange(WT_decile,1,2) & vill_tag, detail
local pop_p50_1 = string(r(p50),"%9.0f")
local pop_p90_1 = string(r(p90),"%9.0f")
sum frame_pop if inrange(WT_decile,3,10) & vill_tag, detail
local pop_p50_2 = string(r(p50),"%9.0f")
local pop_p90_2 = string(r(p90),"%9.0f")


   // MAKE TABLE
file open tablewrite using "$textab/table_nss_2sls_hours.tex", write text replace
 
file write tablewrite "\begin{table}[p]\centering" _n
file write tablewrite "\caption{District-level DD-IV -- districts with power supply \$\ge 10\$ hours/day}" _n
file write tablewrite "\label{tab:nss_2sls_hours}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\small" _n
file write tablewrite "\begin{tabular}{lccccccccc}" _n
file write tablewrite "\hline" _n
file write tablewrite "& \multicolumn{7}{c}{Expenditure per capita (Rs/month)}  \\ " _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\cline{2-8}\\" _n
file write tablewrite "\vspace{-0.90cm}" _n
file write tablewrite "\\" _n
file write tablewrite "& \multicolumn{3}{c}{Levels} & " _n
file write tablewrite "& \multicolumn{3}{c}{Logs} \\" _n
file write tablewrite "& (1) & (2) & (3) && (4) & (5) & (6) \\" _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\cline{2-4} \cline{6-8}" _n
file write tablewrite "\vspace{-0.20cm}" _n
file write tablewrite "\\" _n
file write tablewrite "\$ \mathbf{1}\big[\text{HH consumes any elec}\big] \$ & " _n
file write tablewrite "$`beta1'$`stars1' & $`beta2'$`stars2' & $`beta3'$`stars3' && $`beta4'$`stars4' & $`beta5'$`stars5' & $`beta6'$`stars6' \\" _n
file write tablewrite "& $(`se1')$ & $(`se2')$ & $(`se3')$ && $(`se4')$ & $(`se5')$ & $(`se6')$ \\" _n
file write tablewrite "[0.8em]" _n
file write tablewrite "95\% confidence & \$[`lci1'\$, & \$[`lci2'\$, & \$[`lci3'\$, && \$[`lci4'\$, & \$[`lci5'\$, & \$[`lci6'\$, \\" _n 
file write tablewrite "& \$~`uci1']\$  & \$~`uci2']\$  & \$~`uci3']\$  && \$~`uci4']\$  & \$~`uci5']\$  & \$~`uci6']\$  \\ " _n 
file write tablewrite "[0.8em]" _n
file write tablewrite "Village weight quintiles & Pooled & 1 & 2--5 && Pooled & 1 & 2--5 \\" _n
file write tablewrite "50th pctile of 2001 pop & `pop_p50_0' & `pop_p50_1' & `pop_p50_2' && `pop_p50_0' & `pop_p50_1' & `pop_p50_2' \\" _n
file write tablewrite "90th pctile of 2001 pop & `pop_p90_0' & `pop_p90_1' & `pop_p90_2' && `pop_p90_0' & `pop_p90_1' & `pop_p90_2' \\" _n
file write tablewrite "[0.8em]" _n
file write tablewrite "Mean of dep var & `ymean1' & `ymean2' & `ymean3' && `ymean4' & `ymean5' & `ymean6' \\" _n
file write tablewrite "Clusters & `nclust1' & `nclust2' & `nclust3' && `nclust4' & `nclust5' & `nclust6' \\" _n
file write tablewrite "Observations & `nobs1' & `nobs2' & `nobs3' && `nobs4' & `nobs5' & `nobs6' \\" _n
file write tablewrite "[0.3em]" _n
file write tablewrite "\hline" _n
file write tablewrite "\vspace{-3mm}" _n
file write tablewrite "\\" _n
file write tablewrite "First-stage estimate &  " _n
file write tablewrite "$`beta7'$`stars7' & $`beta8'$`stars8' & $`beta9'$`stars9' && $`beta7'$`stars7' & $`beta8'$`stars8' & $`beta9'$`stars9' \\" _n
file write tablewrite "~~(standard error) & $(`se7')$ & $(`se8')$ & $(`se9')$ && $(`se7')$ & $(`se8')$ & $(`se9')$ \\" _n
file write tablewrite "[0.5em]"
file write tablewrite "First-stage \$F\$-statistic & `fstat1' & `fstat2' & `fstat3' && `fstat4' & `fstat5' & `fstat6' \\" _n
file write tablewrite "\hline" _n
file write tablewrite "\end{tabular}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\caption*{\scriptsize Note. --- Regressions are identical to those in Table \ref*{tab:nss_2sls}, " _n
file write tablewrite "except that they isolate the subset of districts where rural households receive (on average)  " _n
file write tablewrite "at least 10 hours per day of power supply. " _n
file write tablewrite "We calculate this variable by averaging hours of domestic power (from the 2011 Census, at the village level) " _n
file write tablewrite "over all electrified villages in each district. " _n
file write tablewrite "All regressions include: district fixed effects; year fixed effects; " _n
file write tablewrite "linear trends in state quartiles of 2005 household expenditures per capita; " _n 
file write tablewrite "and linear trends in national deciles of 2005 household expenditures per capita. " _n
file write tablewrite "Standard errors are clustered at the district level, collapsing to a " _n
file write tablewrite "single cluster for (i) districts that split in the 2001 Census, but which " _n
file write tablewrite "the 2000 NSS sampled based on 1991 district definitions; and (ii) the few cases " _n
file write tablewrite "where an RGGVY DPR included multiple districts." _n
file write tablewrite "The bottom three rows report the first-stage point estimates and standard errors, along with " _n
file write tablewrite "Kleibergen-Paap first-stage \$F\$-statistics. " _n
file write tablewrite "Significance: *** \$p < 0.01\$, ** \$p < 0.05\$, * \$p < 0.10\$." _n
file write tablewrite "}" _n
file write tablewrite "\end{table}" _n

file close tablewrite

}

********************************************************************************
********************************************************************************

** Table A24: NSS reduced-form DD, levels and logs, split by weight quintile
{
cap file close tablewrite
use "$results/nss_reg_results.dta", clear
keep if panel=="district-year collapsed"
keep if regs=="ols"
keep if inlist(yvar,"mth_pc_expE1","log_exp_30E1")
keep if inlist(ytag,"","_dec12","_dec30")
keep if ifs==""
keep if inlist(fes,"year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt") 

gen c = .
replace c = 1 if yvar=="mth_pc_expE1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag==""
replace c = 2 if yvar=="mth_pc_expE1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_dec12"
replace c = 3 if yvar=="mth_pc_expE1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_dec30"	
replace c = 4 if yvar=="log_exp_30E1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag==""	
replace c = 5 if yvar=="log_exp_30E1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_dec12"	
replace c = 6 if yvar=="log_exp_30E1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_dec30"	
assert c!=.	
sort c

forvalues c = 1/3 {

	local beta`c' = string(beta[`c'],"%9.2f")
	local se`c' = string(se[`c'],"%9.2f")
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if  pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}

	local lci`c' = string(ci95_lo[`c'],"%9.2f")
	local uci`c' = string(ci95_hi[`c'],"%9.2f")
	local ymean`c' = string(ymean_pooled[`c'],"%9.2f")

	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']
	local fstat`c' = string(fstat[`c'],"%9.2f")
}

forvalues c = 4/6 {

	local beta`c' = string(beta[`c'],"%9.3f")
	local se`c' = string(se[`c'],"%9.3f")
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if  pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}

	local lci`c' = string(ci95_lo[`c'],"%9.3f")
	local uci`c' = string(ci95_hi[`c'],"%9.3f")
	local ymean`c' = string(ymean_pooled[`c'],"%9.3f")

	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']
	local fstat`c' = string(fstat[`c'],"%9.2f")
}
	
   // MAKE TABLE
file open tablewrite using "$textab/table_nss_reduced_form_quintiles.tex", write text replace
 
file write tablewrite "\begin{table}[p]\centering" _n
file write tablewrite "\caption{District-level DD -- reduced form by village weight quintiles}" _n
file write tablewrite "\label{tab:nss_reduced_form_quintiles}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\small" _n
file write tablewrite "\begin{tabular}{lccccccccc}" _n
file write tablewrite "\hline" _n
file write tablewrite "& \multicolumn{7}{c}{Expenditure per capita (Rs/month)}  \\ " _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\cline{2-8}\\" _n
file write tablewrite "\vspace{-0.90cm}" _n
file write tablewrite "\\" _n
file write tablewrite "& \multicolumn{3}{c}{Levels} & " _n
file write tablewrite "& \multicolumn{3}{c}{Logs} \\" _n
file write tablewrite "& (1) & (2) & (3) && (4) & (5) & (6) \\" _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\cline{2-4} \cline{6-8}" _n
file write tablewrite "\vspace{-0.20cm}" _n
file write tablewrite "\\" _n
file write tablewrite "$\mathbf{1}\big[\text{10th-Plan district}\big] \times \mathbf{1}\big[2010\big]$~~~ & " _n
file write tablewrite "$`beta1'$`stars1' & $`beta2'$`stars2' & $`beta3'$`stars3' && $`beta4'$`stars4' & $`beta5'$`stars5' & $`beta6'$`stars6' \\ " _n
file write tablewrite "& $(`se1')$ & $(`se2')$ & $(`se3')$ && $(`se4')$ & $(`se5')$ & $(`se6')$  \\" _n
file write tablewrite "[0.8em]" _n
file write tablewrite "Village weight quintiles & Pooled & 1 & 2--5 && Pooled & 1 & 2--5 \\" _n
file write tablewrite "[0.8em]" _n
file write tablewrite "Mean of dep var & `ymean1' & `ymean2' & `ymean3' && `ymean4' & `ymean5' & `ymean6'  \\" _n
file write tablewrite "Clusters & `nclust1' & `nclust2' & `nclust3' && `nclust4' & `nclust5' & `nclust6'  \\" _n
file write tablewrite "Observations & `nobs1' & `nobs2' & `nobs3' && `nobs4' & `nobs5' & `nobs6'  \\" _n
file write tablewrite "\hline" _n
file write tablewrite "\end{tabular}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\caption*{\scriptsize Note. ---  " _n
file write tablewrite "These regressions are the reduced form analogs of the regressions in Table \ref*{tab:nss_2sls}. " _n
file write tablewrite "Expenditures per capita are denominated in 2010 rupees, and net out per capita spending on electricity." _n
file write tablewrite "All regressions include: district fixed effects; year fixed effects; " _n
file write tablewrite "linear trends in state quartiles of 2005 household expenditures per capita; " _n 
file write tablewrite "and linear trends in national deciles of 2005 household expenditures per capita. " _n
file write tablewrite "Standard errors are clustered at the district level, collapsing to a " _n
file write tablewrite "single cluster for (i) districts that split in the 2001 Census, but which " _n
file write tablewrite "the 2000 NSS sampled based on 1991 district definitions; and (ii) the few cases " _n
file write tablewrite "where an RGGVY DPR included multiple districts." _n
file write tablewrite "Significance: *** \$p < 0.01\$, ** \$p < 0.05\$, * \$p < 0.10\$." _n
file write tablewrite "}" _n
file write tablewrite "\end{table}" _n

file close tablewrite

}

********************************************************************************
********************************************************************************

** Table A27: NSS first-stage DD, splitting on expenditure quartiles
{
cap file close tablewrite
use "$results/nss_reg_results.dta", clear
keep if panel=="district-year uncollapsed"
keep if regs=="ols, uncollapsed"
keep if inlist(yvar,"elec_quantity","elec_q_yn")
keep if inlist(fes,"year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt")

gen c = .
replace c = 1 if yvar=="elec_quantity" & ifs==" if exp_quartile==1"
replace c = 2 if yvar=="elec_quantity" & ifs==" if exp_quartile==2"
replace c = 3 if yvar=="elec_quantity" & ifs==" if exp_quartile==3"
replace c = 4 if yvar=="elec_quantity" & ifs==" if exp_quartile==4"
replace c = 5 if yvar=="elec_q_yn" & ifs==" if exp_quartile==1"
replace c = 6 if yvar=="elec_q_yn" & ifs==" if exp_quartile==2"
replace c = 7 if yvar=="elec_q_yn" & ifs==" if exp_quartile==3"
replace c = 8 if yvar=="elec_q_yn" & ifs==" if exp_quartile==4"
assert c!=.	
sort c

foreach c in 1 2 3 4 {

	local beta`c' = string(beta[`c'],"%9.2f")
	local se`c' = string(se[`c'],"%9.2f")
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}
	
	local pval`c' = string(pvalue[`c'],"%9.3f")
	
	local lci`c' = string(ci95_lo[`c'],"%9.2f")
	local uci`c' = string(ci95_hi[`c'],"%9.2f")

	local ymean`c' = string(ymean_pooled[`c'],"%9.2f")
	local nobs`c' = string(nobs[`c'],"%9.0fc")
	local nclust`c' = nclust[`c']

	local exp_max`c' = string(exp_cap[`c'],"%9.0fc")
}

foreach c in 5 6 7 8 {

	local beta`c' = string(beta[`c'],"%9.3f")
	local se`c' = string(se[`c'],"%9.3f")
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}

	local pval`c' = string(pvalue[`c'],"%9.3f")

	local lci`c' = string(ci95_lo[`c'],"%9.3f")
	local uci`c' = string(ci95_hi[`c'],"%9.3f")

	local ymean`c' = string(ymean_pooled[`c'],"%9.3f")
	local nobs`c' = string(nobs[`c'],"%9.0fc")
	local nclust`c' = nclust[`c']
	
	local exp_max`c' = string(exp_cap[`c'],"%9.0fc")
}


use "$panel/panel_dataset_dd_nss_uncollapsed.dta", clear
egen vill_tag = tag(fsu_serial st_code dt_code year)
sum frame_pop if frame_pop<=2000 & vill_tag, detail
local pop_p50 = string(r(p50),"%9.0f")
local pop_p90 = string(r(p90),"%9.0f")


   // MAKE TABLE
file open tablewrite using "$textab/table_nss_first_stage_by_exp_quartile.tex", write text replace
 
file write tablewrite "\begin{table}[h!]\centering" _n
file write tablewrite "\caption{First-stage DD estimates split by household expenditure quartiles}" _n
file write tablewrite "\label{tab:nss_first_stage_by_exp_quartile}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\centerline{" _n
file write tablewrite "\begin{tabular}{lcccccccccccc}" _n
file write tablewrite "\hline" _n
file write tablewrite "& \multicolumn{4}{c}{kWh/month} & " _n
file write tablewrite "& \multicolumn{4}{c}{\$\mathbf{1}\big[\text{kWh}>0]\$} \\ " _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\cline{2-5} \cline{7-10} \\" _n
file write tablewrite "\vspace{-0.90cm}" _n
file write tablewrite "\\" _n
file write tablewrite "& (1) & (2) & (3) & (4) && (5) & (6) & (7) & (8) \\" _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\hline" _n
file write tablewrite "\vspace{-0.20cm}" _n
file write tablewrite "\\" _n
file write tablewrite "$\mathbf{1}\big[\text{10th-Plan}\big] $ & " _n
file write tablewrite "$`beta1'$`stars1' & $`beta2'$`stars2' & $`beta3'$`stars3' & $`beta4'$`stars4' && " _n
file write tablewrite "$`beta5'$`stars5' & $`beta6'$`stars6' & $`beta7'$`stars7' & $`beta8'$`stars8' \\" _n
file write tablewrite "$~~ \times \, \mathbf{1}\big[2010\big]$ & " _n
file write tablewrite "$(`se1')$ & $(`se2')$ & $(`se3')$ & $(`se4')$ && $(`se5')$ & $(`se6')$ & $(`se7')$ & $(`se8')$ \\" _n
file write tablewrite "[0.8em]" _n
file write tablewrite "Expenditure quartile & 1 & 2 & 3 & 4 && 1 & 2 & 3 & 4 \\  " _n
file write tablewrite "Max Rs/month & `exp_max1' & `exp_max2' & `exp_max3' & `exp_max4' && `exp_max5' & `exp_max6' & `exp_max7' & `exp_max8' \\  " _n
file write tablewrite "[0.8em]" _n
file write tablewrite "Mean of dep var & `ymean1' & `ymean2' & `ymean3' & `ymean4' && `ymean5' & `ymean6' & `ymean7' & `ymean8' \\" _n
file write tablewrite "Clusters & `nclust1' & `nclust2' & `nclust3' & `nclust4' && `nclust5' & `nclust6' & `nclust7' & `nclust8' \\" _n
file write tablewrite "Observations & `nobs1' & `nobs2' & `nobs3' & `nobs4' && `nobs5' & `nobs6' & `nobs7' & `nobs8' \\" _n
file write tablewrite "\hline" _n
file write tablewrite "\end{tabular}" _n
file write tablewrite "}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\caption*{\scriptsize Note. --- District-level DD-IV with three NSS years (2000, 2005, 2010), " _n
file write tablewrite "splitting the uncollapsed panel of NSS households by quartiles of household monthly expenditure. " _n
file write tablewrite "While all other NSS regressions collapse to a district-year panel using NSS sampling weights, " _n
file write tablewrite "these regressions use a household-year panel with nationally representative regression weights: " _n
file write tablewrite "NSS sampling weights (representative at the district level) multiplied by each district's rural population. " _n
file write tablewrite "The outcome variables are the household's monthly electricity consumption, and " _n
file write tablewrite "an indicator for whether the household consumed any electricity." _n
file write tablewrite "Expenditure quartiles are net of spending on electricity. " _n
file write tablewrite "We divide the point estimates in Columns (1)--(4) by the point estimates in Columns (5)--(8) " _n 
file write tablewrite "to construct quartile-specific estimates of kWh/month per newly electrified household, " _n 
file write tablewrite "which serve as an input to rows 4--6 of Table \ref*{tab:irr_cs}. " _n 
file write tablewrite "All regressions include: district fixed effects; year fixed effects; state-specific linear trends; " _n
file write tablewrite "linear trends in state quartiles of 2005 household expenditures per capita; " _n 
file write tablewrite "and linear trends in national deciles of 2005 household expenditures per capita. " _n
file write tablewrite "Standard errors are clustered at the district level, collapsing to a " _n
file write tablewrite "single cluster for (i) districts that split in the 2001 Census, but which " _n
file write tablewrite "the 2000 NSS sampled based on 1991 district definitions; and (ii) the few cases " _n
file write tablewrite "where an RGGVY DPR included multiple districts." _n
file write tablewrite "Significance: *** \$p < 0.01\$, ** \$p < 0.05\$, * \$p < 0.10\$." _n
file write tablewrite "}" _n
file write tablewrite "\end{table}" _n

file close tablewrite

}

********************************************************************************
********************************************************************************

** Table A29: NSS 2SLS DD, levels and logs, <2000 population, 2005-10 waves
{
cap file close tablewrite
use "$results/nss_reg_results.dta", clear
keep if panel=="district-year collapsed"
keep if (regs=="iv" & inlist(yvar,"mth_pc_expE1","log_exp_30E1")) | (regs=="ols" & inlist(yvar,"elec_q_yn"))
keep if inlist(ytag,"_under2k")
keep if ifs==""
keep if inlist(fes,"year stdt","year c.year#exp05_st_4ile stdt","year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt")

gen c = .
replace c = 1 if yvar=="mth_pc_expE1" & fes=="year stdt" & ytag=="_under2k"
replace c = 2 if yvar=="mth_pc_expE1" & fes=="year c.year#exp05_st_4ile stdt" & ytag=="_under2k"
replace c = 3 if yvar=="mth_pc_expE1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_under2k"
replace c = 4 if yvar=="log_exp_30E1" & fes=="year stdt" & ytag=="_under2k"
replace c = 5 if yvar=="log_exp_30E1" & fes=="year c.year#exp05_st_4ile stdt" & ytag=="_under2k"
replace c = 6 if yvar=="log_exp_30E1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_under2k"
replace c = 7 if yvar=="elec_q_yn" & fes=="year stdt" & ytag=="_under2k"
replace c = 8 if yvar=="elec_q_yn" & fes=="year c.year#exp05_st_4ile stdt" & ytag=="_under2k"
replace c = 9 if yvar=="elec_q_yn" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_under2k"
assert c!=.	
sort c

forvalues c = 1/3 {
		
	local beta`c' = string(beta[`c'],"%9.1f")
	local se`c' = string(se[`c'],"%9.1f")
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if  pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}
	
	local lci`c' = string(ci95_lo[`c'],"%9.1f")
	local uci`c' = string(ci95_hi[`c'],"%9.1f")
	local ymean`c' = string(ymean_pooled[`c'],"%9.1f")

	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']
	local fstat`c' = string(fstat[`c'],"%9.2f")
}	
	
forvalues c = 4/6 {

	local beta`c' = string(beta[`c'],"%9.3f")
	local se`c' = string(se[`c'],"%9.3f")
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if  pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}

	local lci`c' = string(ci95_lo[`c'],"%9.3f")
	local uci`c' = string(ci95_hi[`c'],"%9.3f")
	local ymean`c' = string(ymean_pooled[`c'],"%9.3f")

	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']
	local fstat`c' = string(fstat[`c'],"%9.2f")
}
	
forvalues c = 7/9 {

	local beta`c' = string(beta[`c'],"%9.3f")
	local se`c' = string(se[`c'],"%9.3f")
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if  pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}
}

use "$panel/panel_dataset_dd_nss_uncollapsed.dta", clear
egen vill_tag = tag(fsu_serial st_code dt_code year)
sum frame_pop if frame_pop<=2000 & vill_tag, detail
local pop_p50 = string(r(p50),"%9.0f")
local pop_p90 = string(r(p90),"%9.0f")


   // MAKE TABLE
file open tablewrite using "$textab/table_nss_2sls_under2k.tex", write text replace
 
file write tablewrite "\begin{table}[h!]\centering" _n
file write tablewrite "\caption{District-level DD-IV of consumption expenditures -- sub-2000-person villages}" _n
file write tablewrite "\label{tab:nss_2sls_under2k}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\begin{tabular}{lccccccccc}" _n
file write tablewrite "\hline" _n
file write tablewrite "& \multicolumn{7}{c}{Expenditure per capita (Rs/month)}  \\ " _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\cline{2-8}\\" _n
file write tablewrite "\vspace{-0.90cm}" _n
file write tablewrite "\\" _n
file write tablewrite "& \multicolumn{3}{c}{Levels} & " _n
file write tablewrite "& \multicolumn{3}{c}{Logs} \\" _n
file write tablewrite "& (1) & (2) & (3) && (4) & (5) & (6) \\" _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\cline{2-4} \cline{6-8}" _n
file write tablewrite "\vspace{-0.20cm}" _n
file write tablewrite "\\" _n
file write tablewrite "\$ \mathbf{1}\big[\text{HH consumes any elec}\big] \$ & " _n
file write tablewrite "$`beta1'$`stars1' & $`beta2'$`stars2' & $`beta3'$`stars3' && $`beta4'$`stars4' & $`beta5'$`stars5' & $`beta6'$`stars6' \\" _n
file write tablewrite "& $(`se1')$ & $(`se2')$ & $(`se3')$ && $(`se4')$ & $(`se5')$ & $(`se6')$ \\" _n
file write tablewrite "[0.8em]" _n
file write tablewrite "95\% confidence & \$[`lci1'\$, & \$[`lci2'\$, & \$[`lci3'\$, && \$[`lci4'\$, & \$[`lci5'\$, & \$[`lci6'\$, \\" _n 
file write tablewrite "                & \$~`uci1']\$  & \$~`uci2']\$  & \$~`uci3']\$  && \$~`uci4']\$  & \$~`uci5']\$  & \$~`uci6']\$  \\ " _n 
file write tablewrite "[0.8em]" _n
file write tablewrite "Village population (2001) & \$\le\$\,2000 & \$\le\$\,2000 & \$\le\$\,2000 && \$\le\$\,2000 & \$\le\$\,2000 & \$\le\$\,2000 \\" _n
file write tablewrite "50th pctile of 2001 pop & `pop_p50' & `pop_p50' & `pop_p50' && `pop_p50' & `pop_p50' & `pop_p50' \\" _n
file write tablewrite "90th pctile of 2001 pop & `pop_p90' & `pop_p90' & `pop_p90' && `pop_p90' & `pop_p90' & `pop_p90' \\" _n
file write tablewrite "[0.8em]" _n
file write tablewrite "Linear trends by: \\ " _n
file write tablewrite "~~~State exp.\ quartiles &  & Yes & Yes &&  & Yes & Yes \\" _n
file write tablewrite "~~~Nat'l exp.\ deciles &  &   & Yes &&  &  & Yes \\" _n
file write tablewrite "[0.5em]" _n
file write tablewrite "Mean of dep var & `ymean1' & `ymean2' & `ymean3' && `ymean4' & `ymean5' & `ymean6' \\" _n
file write tablewrite "Clusters & `nclust1' & `nclust2' & `nclust3' && `nclust4' & `nclust5' & `nclust6' \\" _n
file write tablewrite "Observations & `nobs1' & `nobs2' & `nobs3' && `nobs4' & `nobs5' & `nobs6' \\" _n
file write tablewrite "[0.3em]" _n
file write tablewrite "\hline" _n
file write tablewrite "\vspace{-3mm}" _n
file write tablewrite "\\" _n
file write tablewrite "First-stage estimate &  " _n
file write tablewrite "$`beta7'$`stars7' & $`beta8'$`stars8' & $`beta9'$`stars9' && $`beta7'$`stars7' & $`beta8'$`stars8' & $`beta9'$`stars9' \\" _n
file write tablewrite "~~(standard error) & $(`se7')$ & $(`se8')$ & $(`se9')$ && $(`se7')$ & $(`se8')$ & $(`se9')$ \\" _n
file write tablewrite "[0.5em]"
file write tablewrite "First-stage \$F\$-statistic & `fstat1' & `fstat2' & `fstat3' && `fstat4' & `fstat5' & `fstat6' \\" _n
file write tablewrite "\hline" _n
file write tablewrite "\end{tabular}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\caption*{\scriptsize Note. --- District-level DD-IV with two NSS years (2005, 2010), " _n
file write tablewrite "splitting on 2001 village population before collapsing to the district level using NSS sampling weights. " _n
file write tablewrite "We do not observe village populations in the 2000 NSS wave, meaning that in order to estimate a 3-period panel " _n
file write tablewrite "that removes extremely large villages, we can only split on the distribution of village weights. " _n
file write tablewrite "These regressions include NSS villages with 2000 or fewer people in 2001, with results that compare favorably " _n
file write tablewrite "to Columns (2) and (5) of Table \ref*{tab:nss_2sls} (over similar population supports). " _n
file write tablewrite "Regressions are otherwise identical to those in Table \ref*{tab:nss_2sls}, except for fewer linear trends in " _n
file write tablewrite "in Columns (1)--(2) and (4)--(5). Including both sets of linear trends in expenditure causes our " _n
file write tablewrite "\$F\$-statistics in the 2-period panel to drop below the Stock-Yogo critical value of 16.38. " _n 
file write tablewrite "Since these trends help our identification, we report the 3-period panels as our main results. " _n
file write tablewrite "All regressions include district fixed effects and year fixed effects. " _n
file write tablewrite "Standard errors are clustered at the district level, collapsing to a " _n
file write tablewrite "single cluster for (i) districts that split in the 2001 Census, but which " _n
file write tablewrite "the 2000 NSS sampled based on 1991 district definitions; and (ii) the few cases " _n
file write tablewrite "where an RGGVY DPR included multiple districts." _n
file write tablewrite "The bottom three rows report the first-stage point estimates and standard errors, along with " _n
file write tablewrite "Kleibergen-Paap first-stage \$F\$-statistics. " _n
file write tablewrite "Significance: *** \$p < 0.01\$, ** \$p < 0.05\$, * \$p < 0.10\$." _n
file write tablewrite "}" _n
file write tablewrite "\end{table}" _n

file close tablewrite

}

********************************************************************************
********************************************************************************

** Table B7: NSS first-stage pre-trends, extensive and intensive margins + appliances
{
cap file close tablewrite
use "$results/nss_reg_results.dta", clear
keep if panel=="district-year collapsed"
keep if regs=="ols (pretrends)"
keep if inlist(yvar,"elec_q_yn","log_elec_q","elec_quantity","elec_light","fan","tv","fridge","ac")
keep if ytag==""
keep if ifs==" if year<2010"
keep if inlist(fes,"year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt")

gen c = .
replace c = 1 if yvar=="elec_q_yn"	
replace c = 2 if yvar=="elec_quantity" 
replace c = 3 if yvar=="log_elec_q"
replace c = 4 if yvar=="elec_light"
replace c = 5 if yvar=="fan" 
replace c = 6 if yvar=="tv" 
replace c = 7 if yvar=="fridge"
replace c = 8 if yvar=="ac" 	
assert c!=.	
sort c

forvalues c = 1/8 {
	
	if `c'!=2 {
		local beta`c' = string(beta[`c'],"%9.3f")
		local se`c' = string(se[`c'],"%9.3f")
	}
	else {
	    local beta`c' = string(beta[`c'],"%9.2f")
		local se`c' = string(se[`c'],"%9.2f")
	}
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if  pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}

	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']
	if `c'!=2 {
		local ymean`c' = string(ymean_pooled[`c'],"%9.3f")
	}
	else {
		local ymean`c' = string(ymean_pooled[`c'],"%9.2f")    
	}
}	
	
   // MAKE TABLE
file open tablewrite using "$textab/table_nss_first_stage_pretrends.tex", write text replace
 
file write tablewrite "\begin{table}[h!]\centering" _n
file write tablewrite "\caption{Pre-trends for district-level DD in household electricity access and usage}" _n
file write tablewrite "\label{tab:nss_first_stage_pretrends}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\small" _n
file write tablewrite "\begin{tabular}{lccccccccccc}" _n
file write tablewrite "\hline" _n
file write tablewrite "& \multicolumn{3}{c}{HH elec use (kWh/month)} "  _n
file write tablewrite "&& \multicolumn{5}{c}{\$ \mathbf{1}\big[\text{HH owns electric appliance}\big] \$} \\ "  _n
file write tablewrite "\cline{2-4} \cline{6-10}\\" _n
file write tablewrite "\vspace{-0.90cm}" _n
file write tablewrite "\\" _n
file write tablewrite "& \$ \mathbf{1}\big[Q > 0\big] \$ & Levels & Logs && Lighting & Fan & TV & Fridge & AC \\" _n
file write tablewrite "& (1) & (2) & (3) && (4) & (5) & (6) & (7) & (8) \\" _n
file write tablewrite "\hline" _n
file write tablewrite "\vspace{-0.40cm}" _n
file write tablewrite "\\" _n
file write tablewrite "$\mathbf{1}\big[\text{10th-Plan}\big] \$ & " _n
file write tablewrite "$`beta1'$`stars1' & $`beta2'$`stars2' & $`beta3'$`stars3' && $`beta4'$`stars4' & $`beta5'$`stars5' & $`beta6'$`stars6' & $`beta7'$`stars7' & $`beta8'$`stars8' \\" _n
file write tablewrite "$ ~~\times \, \mathbf{1}\big[2005\big] \$ & $(`se1')$ & $(`se2')$ & $(`se3')$ && $(`se4')$ & $(`se5')$ & $(`se6')$  & $(`se7')$  & $(`se8')$ \\" _n
file write tablewrite "[0.8em]" _n
file write tablewrite "Mean of dep var & `ymean1' & `ymean2' & `ymean3' && `ymean4' & `ymean5' & `ymean6' & `ymean7' & `ymean8' \\" _n
file write tablewrite "Clusters & `nclust1' & `nclust2' & `nclust3' && `nclust4' & `nclust5' & `nclust6' & `nclust7' & `nclust8' \\" _n
file write tablewrite "Observations & `nobs1' & `nobs2' & `nobs3' && `nobs4' & `nobs5' & `nobs6' & `nobs7' & `nobs8' \\" _n
file write tablewrite "\hline" _n
file write tablewrite "\end{tabular}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\caption*{\scriptsize Note. --- District-level DD with two NSS years (2000, 2005), using 2005 " _n
file write tablewrite " (rather than 2010) as a \`\`post'' period to test for differential pre-treatment trends. " _n
file write tablewrite "Regressions are otherwise identical to those in Table \ref*{tab:nss_first_stage}. " _n
file write tablewrite "All regressions include: district fixed effects; year fixed effects; state-specific linear trends; " _n
file write tablewrite "linear trends in state quartiles of 2005 household expenditures per capita; " _n 
file write tablewrite "and linear trends in national deciles of 2005 household expenditures per capita. " _n
file write tablewrite "Standard errors are clustered at the district level, collapsing to a " _n
file write tablewrite "single cluster for (i) districts that split in the 2001 Census, but which " _n
file write tablewrite "the 2000 NSS sampled based on 1991 district definitions; and (ii) the few cases " _n
file write tablewrite "where an RGGVY DPR included multiple districts." _n
file write tablewrite "Significance: *** \$p < 0.01\$, ** \$p < 0.05\$, * \$p < 0.10\$." _n
file write tablewrite "}" _n
file write tablewrite "\end{table}" _n

file close tablewrite

}

********************************************************************************
********************************************************************************

** Table B8: NSS reduced-form pre-trends, levels and logs
{
cap file close tablewrite
use "$results/nss_reg_results.dta", clear
keep if panel=="district-year collapsed"
keep if regs=="ols (pretrends)"
keep if inlist(yvar,"mth_pc_expE1","log_exp_30E1")
keep if ytag==""
keep if ifs==" if year<2010"
keep if inlist(fes,"year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt")

gen c = .
replace c = 1 if yvar=="mth_pc_expE1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt"	
replace c = 2 if yvar=="log_exp_30E1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt"	
assert c!=.	
sort c

forvalues c = 1/1 {

	local beta`c' = string(beta[`c'],"%9.2f")
	local se`c' = string(se[`c'],"%9.2f")
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if  pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}

	local lci`c' = string(ci95_lo[`c'],"%9.2f")
	local uci`c' = string(ci95_hi[`c'],"%9.2f")
	local ymean`c' = string(ymean_pooled[`c'],"%9.2f")
	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']
}
	
forvalues c = 2/2 {

	local beta`c' = string(beta[`c'],"%9.3f")
	local se`c' = string(se[`c'],"%9.3f")
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if  pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}

	local lci`c' = string(ci95_lo[`c'],"%9.3f")
	local uci`c' = string(ci95_hi[`c'],"%9.3f")
	local ymean`c' = string(ymean_pooled[`c'],"%9.3f")
	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']
}
	
   // MAKE TABLE
file open tablewrite using "$textab/table_nss_reduced_form_pretrends.tex", write text replace
 
file write tablewrite "\begin{table}[h!]\centering" _n
file write tablewrite "\caption{Pre-trends for district-level DD of household consumption expenditures}" _n
file write tablewrite "\label{tab:nss_reduced_form_pretrends}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\small" _n
file write tablewrite "\begin{tabular}{lccccccccc}" _n
file write tablewrite "\hline" _n
file write tablewrite "& \multicolumn{3}{c}{Expenditure per capita (Rs/month)}  \\ " _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\cline{2-4}\\" _n
file write tablewrite "\vspace{-0.90cm}" _n
file write tablewrite "\\" _n
file write tablewrite "& \multicolumn{1}{c}{~~~~~~~~~~Levels~~~~~~~~~~} & " _n
file write tablewrite "& \multicolumn{1}{c}{Logs} \\" _n
file write tablewrite "& (1) & & (2) \\" _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\hline" _n
file write tablewrite "\vspace{-0.20cm}" _n
file write tablewrite "\\" _n
file write tablewrite "$\mathbf{1}\big[\text{10th-Plan}\big] \times \mathbf{1}\big[2005\big]$ & " _n
file write tablewrite "$`beta1'$`stars1' && $`beta2'$`stars2' \\" _n
file write tablewrite "& $(`se1')$ && $(`se2')$  \\" _n
file write tablewrite "[0.8em]" _n
file write tablewrite "Mean of dep var & `ymean1' && `ymean2' \\" _n
file write tablewrite "Clusters & `nclust1' && `nclust2'  \\" _n
file write tablewrite "Observations & `nobs1' && `nobs2' \\" _n
file write tablewrite "\hline" _n
file write tablewrite "\end{tabular}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\caption*{\scriptsize Note. --- District-level DD with two NSS years (2000, 2005), using 2005 " _n
file write tablewrite " (rather than 2010) as a \`\`post'' period to test for differential pre-treatment trends. " _n
file write tablewrite "Regressions are otherwise identical to those in Table \ref*{tab:nss_reduced_form}. " _n
file write tablewrite "Expenditures per capita are denominated in 2010 rupees, and net out per capita spending on electricity." _n
file write tablewrite "All regressions include: district fixed effects; year fixed effects; state-specific linear trends; " _n
file write tablewrite "linear trends in state quartiles of 2005 household expenditures per capita; " _n 
file write tablewrite "and linear trends in national deciles of 2005 household expenditures per capita. " _n
file write tablewrite "Standard errors are clustered at the district level, collapsing to a " _n
file write tablewrite "single cluster for (i) districts that split in the 2001 Census, but which " _n
file write tablewrite "the 2000 NSS sampled based on 1991 district definitions; and (ii) the few cases " _n
file write tablewrite "where an RGGVY DPR included multiple districts." _n
file write tablewrite "Significance: *** \$p < 0.01\$, ** \$p < 0.05\$, * \$p < 0.10\$." _n
file write tablewrite "}" _n
file write tablewrite "\end{table}" _n

file close tablewrite

}

********************************************************************************
********************************************************************************

** Figure B9: NSS first-stage randomization test
{
cap file close tablewrite
use "$results/nss_reg_results.dta", clear
keep if panel=="district-year collapsed"
keep if regs=="ols"
keep if inlist(yvar,"elec_q_yn","log_elec_q","elec_quantity")
keep if ytag==""
keep if ifs==""
keep if inlist(fes,"year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt")

gen c = .
replace c = 1 if yvar=="elec_q_yn" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt"	
replace c = 2 if yvar=="elec_quantity" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt"	
replace c = 3 if yvar=="log_elec_q" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt"	
assert c!=.	
sort c

local beta1 = beta[1]
local beta2 = beta[2]
local beta3 = beta[3]
	
use "$sens/nss_dd_randomization_test.dta", clear

di `beta1'
sum beta_extens_st_trends, detail
_pctile beta_extens_st_trends , p(99(.1)99.9)
return list // above 99.9th percentile

di `beta2'
sum beta_levels_st_trends, detail
_pctile beta_levels_st_trends , p(99(.1)99.9)
return list // above 99.9th percentile

di `beta3'
sum beta_logs_st_trends, detail
_pctile beta_logs_st_trends , p(99(.1)99.9)
return list // above 99.8th percentile



twoway (histogram beta_extens_st_trends, freq fcolor(navy) lcolor(black)) ///
       (scatteri 0 `beta1' 800 `beta1', msize(0) mcolor(red) connect(l) lwidth(medthick) lcolor(red)), ///  
       xlabel(, labsize(medlarge)) ///
       ytitle("Count", size(medlarge)) title("NSS first stage, extensive margin", size(vlarge) color(black)) ///
			 legend(off) ylabel(,nogrid angle(0) labsize(medlarge)) ///
			 xtitle("DD coefficients randomizing RGGVY rollout", size(large)) ///
			 graphregion(lcolor(white)) graphregion(color(white)) plotregion(fcolor(white)) aspect(0.75) 
graph export "$texfig/randomization_test_nss_extens_st_trends.pdf", replace 

twoway (histogram beta_levels_st_trends, freq fcolor(navy) lcolor(black)) ///
       (scatteri 0 `beta2' 800 `beta2', msize(0) mcolor(red) connect(l) lwidth(medthick) lcolor(red)), ///  
       xlabel(, labsize(medlarge)) ///
       ytitle("", size(medlarge)) title("NSS first stage, kWh", size(vlarge) color(black)) ///
			 legend(off) ylabel(,nogrid angle(0) labsize(medlarge)) ///
			 xtitle("DD coefficients randomizing RGGVY rollout", size(large)) ///
			 graphregion(lcolor(white)) graphregion(color(white)) plotregion(fcolor(white)) aspect(0.75) 
graph export "$texfig/randomization_test_nss_levels_st_trends.pdf", replace 

twoway (histogram beta_logs_st_trends, freq fcolor(navy) lcolor(black)) ///
       (scatteri 0 `beta3' 800 `beta3', msize(0) mcolor(red) connect(l) lwidth(medthick) lcolor(red)), ///  
       xlabel(, labsize(medlarge)) ///
       ytitle("", size(medlarge)) title("NSS first stage, log(kWh)", size(vlarge) color(black)) ///
			 legend(off) ylabel(,nogrid angle(0) labsize(medlarge)) ///
			 xtitle("DD coefficients randomizing RGGVY rollout", size(large)) ///
			 graphregion(lcolor(white)) graphregion(color(white)) plotregion(fcolor(white)) aspect(0.75)
graph export "$texfig/randomization_test_nss_logs_st_trends.pdf", replace 


   // MAKE FIGURE
file open tablewrite using "$texfig/figure_nss_randomization.tex", write text replace
 
file write tablewrite "\begin{figure}[h!]\centering" _n
file write tablewrite "\caption{Randomization tests for household electricity consumption}" _n
file write tablewrite "\label{fig:nss_randomization}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "{\includegraphics[width=0.327\textwidth, trim={13mm 0mm 11mm 0mm}, clip]{${texfig_short}/randomization_test_nss_extens_st_trends.pdf}} " _n
file write tablewrite "{\includegraphics[width=0.327\textwidth, trim={13mm 0mm 11mm 0mm}, clip]{${texfig_short}/randomization_test_nss_levels_st_trends.pdf}} " _n
file write tablewrite "{\includegraphics[width=0.327\textwidth, trim={13mm 0mm 11mm 0mm}, clip]{${texfig_short}/randomization_test_nss_logs_st_trends.pdf}} " _n
file write tablewrite "\vspace{-8mm}" _n
file write tablewrite "\caption*{\scriptsize Note. --- Each panel reports the density of  " _n
file write tablewrite "10,000 randomized DD estimates, where each iteration re-estimates our main DD specification " _n
file write tablewrite "after randomly permuting the set of 10th- vs.\ 11th-Plan RGGVY districts. " _n
file write tablewrite "From left to right, panels correspond to Columns (1)--(3) of Table \ref*{tab:nss_first_stage}. " _n
file write tablewrite "The true DD estimates (red dashed lines) each fall above the 99.8th percentile of " _n 
file write tablewrite "their respective randomized distributions." _n
file write tablewrite "}" _n
file write tablewrite "\end{figure}" _n

file close tablewrite


}

********************************************************************************
********************************************************************************

** Table B9: NSS first-stage and reduced-form DD, dropping split districts and non-RGGVY districts
{
cap file close tablewrite
use "$results/nss_reg_results.dta", clear
keep if panel=="district-year collapsed"
keep if regs=="ols"
keep if inlist(yvar,"elec_q_yn","elec_quantity","log_elec_q","mth_pc_expE1","log_exp_30E1")
keep if inlist(ytag,"") //,"_dec12","_dec30")
keep if ifs==" if sample_1011"
keep if inlist(fes,"year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt")

gen c = .
replace c = 1 if yvar=="elec_q_yn"
replace c = 2 if yvar=="elec_quantity"
replace c = 3 if yvar=="log_elec_q" 
replace c = 4 if yvar=="mth_pc_expE1" 
replace c = 5 if yvar=="log_exp_30E1" 
assert c!=.	
sort c

forvalues c = 1/5 {
		
	if inlist(`c',2,4) {
	    local beta`c' = string(beta[`c'],"%9.2f")
		local se`c' = string(se[`c'],"%9.2f")
	}
	else {
	    local beta`c' = string(beta[`c'],"%9.3f")
		local se`c' = string(se[`c'],"%9.3f")
	}
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if  pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}

	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']
	if inlist(`c',2,4) {
		local ymean`c' = string(ymean_pooled[`c'],"%9.2f")
	}
	else {
		local ymean`c' = string(ymean_pooled[`c'],"%9.3f")
	}
}	

   // MAKE TABLE
file open tablewrite using "$textab/table_nss_fs_rf_rggvy_districts.tex", write text replace
 
file write tablewrite "\begin{table}[h!]\centering" _n
file write tablewrite "\caption{District-level DD -- RGGVY single-Plan districts only}" _n
file write tablewrite "\label{tab:nss_fs_rf_rggvy_districts}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\small" _n
file write tablewrite "\begin{tabular}{lccccccccc}" _n
file write tablewrite "\hline" _n
file write tablewrite "& \multicolumn{3}{c}{HH elec use (kWh/month)} && " _n
file write tablewrite "\multicolumn{2}{c}{Exp.\ per capita (Rs/month)} \\ " _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\cline{2-4} \cline{6-7}\\" _n
file write tablewrite "\vspace{-0.90cm}" _n
file write tablewrite "\\" _n
file write tablewrite "& \$\mathbf{1}\big[Q>0\big]\$ & Levels & Logs &&" _n
file write tablewrite "~~~~~Levels~~~~~ & Logs \\" _n
file write tablewrite "& (1) & (2) & (3) && (4) & (5) \\" _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\cline{2-4} \cline{6-7}" _n
file write tablewrite "\vspace{-0.20cm}" _n
file write tablewrite "\\" _n
file write tablewrite "$\mathbf{1}\big[\text{10th-Plan district}\big] \times \mathbf{1}\big[2010\big]$~~ & " _n
file write tablewrite "$`beta1'$`stars1' & $`beta2'$`stars2' & $`beta3'$`stars3' && $`beta4'$`stars4' & $`beta5'$`stars5' \\" _n
file write tablewrite "& $(`se1')$ & $(`se2')$ & $(`se3')$ && $(`se4')$ & $(`se5')$ \\" _n
file write tablewrite "[0.8em]" _n
file write tablewrite "Mean of dep var & `ymean1' & `ymean2' & `ymean3' && `ymean4' & `ymean5' \\" _n
file write tablewrite "Clusters & `nclust1' & `nclust2' & `nclust3' && `nclust4' & `nclust5' \\" _n
file write tablewrite "Observations & `nobs1' & `nobs2' & `nobs3' && `nobs4' & `nobs5'  \\" _n
file write tablewrite "\hline" _n
file write tablewrite "\end{tabular}" _n
file write tablewrite "\vspace{-2mm}" _n
file write tablewrite "\caption*{\scriptsize Note. --- These regressions remove 30 districts from the \`\`treated'' group  " _n
file write tablewrite "that had RGGVY projects in both the 10th and 11th Plans. They also remove 37 districts from the " _n
file write tablewrite "\`\`control'' group that had no RGGVY projects under either Plan. This leaves two \`\`pure'' " _n
file write tablewrite "groups of 199 10th-Plan-only \`\`treated'' districts and 297 11th-Plan-only \`\`control'' districts. " _n
file write tablewrite "Regressions are otherwise identical to Columns (1)--(3) of Table \ref*{tab:nss_first_stage},  " _n
file write tablewrite "and Columns (1)--(2) of Table \ref*{tab:nss_reduced_form}. " _n
file write tablewrite "All regressions include: district fixed effects; year fixed effects; state-specific linear trends; " _n
file write tablewrite "linear trends in state quartiles of 2005 household expenditures per capita; " _n 
file write tablewrite "and linear trends in national deciles of 2005 household expenditures per capita. " _n
file write tablewrite "Standard errors are clustered at the district level, collapsing to a " _n
file write tablewrite "single cluster for (i) districts that split in the 2001 Census, but which " _n
file write tablewrite "the 2000 NSS sampled based on 1991 district definitions; and (ii) the few cases " _n
file write tablewrite "where an RGGVY DPR included multiple districts." _n
file write tablewrite "Significance: *** \$p < 0.01\$, ** \$p < 0.05\$, * \$p < 0.10\$." _n
file write tablewrite "}" _n
file write tablewrite "\end{table}" _n

file close tablewrite

}

********************************************************************************
********************************************************************************

** Table B10: NSS 2SLS DD, levels and logs + state-year trends
{
cap file close tablewrite
use "$results/nss_reg_results.dta", clear
keep if panel=="district-year collapsed"
keep if (regs=="iv" & inlist(yvar,"mth_pc_expE1","log_exp_30E1")) | (regs=="ols" & inlist(yvar,"elec_q_yn"))
keep if inlist(ytag,"","_dec12","_dec30")
keep if ifs==""
keep if inlist(fes,"year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt")

gen c = .
replace c = 1 if yvar=="mth_pc_expE1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt" & ytag==""
replace c = 2 if yvar=="mth_pc_expE1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt" & ytag=="_dec12"
replace c = 3 if yvar=="mth_pc_expE1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt" & ytag=="_dec30"
replace c = 4 if yvar=="log_exp_30E1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt" & ytag==""
replace c = 5 if yvar=="log_exp_30E1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt" & ytag=="_dec12"
replace c = 6 if yvar=="log_exp_30E1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt" & ytag=="_dec30"
replace c = 7 if yvar=="elec_q_yn" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt" & ytag==""
replace c = 8 if yvar=="elec_q_yn" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt" & ytag=="_dec12"
replace c = 9 if yvar=="elec_q_yn" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile c.year#st_code stdt" & ytag=="_dec30"
assert c!=.	
sort c

forvalues c = 1/3 {
		
	local beta`c' = string(beta[`c'],"%9.1f")
	local se`c' = string(se[`c'],"%9.1f")
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if  pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}
	
	local lci`c' = string(ci95_lo[`c'],"%9.1f")
	local uci`c' = string(ci95_hi[`c'],"%9.1f")
	local ymean`c' = string(ymean_pooled[`c'],"%9.1f")

	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']
	local fstat`c' = string(fstat[`c'],"%9.2f")
}	
	
forvalues c = 4/6 {

	local beta`c' = string(beta[`c'],"%9.3f")
	local se`c' = string(se[`c'],"%9.3f")
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if  pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}

	local lci`c' = string(ci95_lo[`c'],"%9.3f")
	local uci`c' = string(ci95_hi[`c'],"%9.3f")
	local ymean`c' = string(ymean_pooled[`c'],"%9.3f")

	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']
	local fstat`c' = string(fstat[`c'],"%9.2f")
}

forvalues c = 7/9 {

	local beta`c' = string(beta[`c'],"%9.3f")
	local se`c' = string(se[`c'],"%9.3f")
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if  pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}
}


use "$panel/panel_dataset_dd_nss_uncollapsed.dta", clear
egen vill_tag = tag(fsu_serial st_code dt_code year)
sum frame_pop if vill_tag, detail
local pop_p50_0 = string(r(p50),"%9.0f")
local pop_p90_0 = string(r(p90),"%9.0f")
sum frame_pop if inrange(WT_decile,1,2) & vill_tag, detail
local pop_p50_1 = string(r(p50),"%9.0f")
local pop_p90_1 = string(r(p90),"%9.0f")
sum frame_pop if inrange(WT_decile,3,10) & vill_tag, detail
local pop_p50_2 = string(r(p50),"%9.0f")
local pop_p90_2 = string(r(p90),"%9.0f")


   // MAKE TABLE
file open tablewrite using "$textab/table_nss_2sls_state_trends.tex", write text replace
 
file write tablewrite "\begin{table}[h!]\centering" _n
file write tablewrite "\caption{District-level DD-IV adding state-specific linear trends}" _n
file write tablewrite "\label{tab:nss_2sls_state_trends}" _n
file write tablewrite "\vspace{-3mm}" _n
file write tablewrite "\small" _n
file write tablewrite "\begin{tabular}{lccccccccc}" _n
file write tablewrite "\hline" _n
file write tablewrite "& \multicolumn{7}{c}{Expenditure per capita (Rs/month)}  \\ " _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\cline{2-8}\\" _n
file write tablewrite "\vspace{-0.90cm}" _n
file write tablewrite "\\" _n
file write tablewrite "& \multicolumn{3}{c}{Levels} & " _n
file write tablewrite "& \multicolumn{3}{c}{Logs} \\" _n
file write tablewrite "& (1) & (2) & (3) && (4) & (5) & (6) \\" _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\cline{2-4} \cline{6-8}" _n
file write tablewrite "\vspace{-0.20cm}" _n
file write tablewrite "\\" _n
file write tablewrite "\$ \mathbf{1}\big[\text{HH consumes any elec}\big] \$ & " _n
file write tablewrite "$`beta1'$`stars1' & $`beta2'$`stars2' & $`beta3'$`stars3' && $`beta4'$`stars4' & $`beta5'$`stars5' & $`beta6'$`stars6' \\" _n
file write tablewrite "& $(`se1')$ & $(`se2')$ & $(`se3')$ && $(`se4')$ & $(`se5')$ & $(`se6')$ \\" _n
file write tablewrite "[0.8em]" _n
file write tablewrite "95\% confidence & \$[`lci1'\$, & \$[`lci2'\$, & \$[`lci3'\$, && \$[`lci4'\$, & \$[`lci5'\$, & \$[`lci6'\$, \\" _n 
file write tablewrite "& \$~`uci1']\$  & \$~`uci2']\$  & \$~`uci3']\$  && \$~`uci4']\$  & \$~`uci5']\$  & \$~`uci6']\$  \\ " _n 
file write tablewrite "[0.5em]" _n
file write tablewrite "Village weight quintiles & Pooled & 1 & 2--5 && Pooled & 1 & 2--5 \\" _n
file write tablewrite "50th pctile of 2001 pop & `pop_p50_0' & `pop_p50_1' & `pop_p50_2' && `pop_p50_0' & `pop_p50_1' & `pop_p50_2' \\" _n
file write tablewrite "90th pctile of 2001 pop & `pop_p90_0' & `pop_p90_1' & `pop_p90_2' && `pop_p90_0' & `pop_p90_1' & `pop_p90_2' \\" _n
file write tablewrite "[0.5em]" _n
file write tablewrite "Mean of dep var & `ymean1' & `ymean2' & `ymean3' && `ymean4' & `ymean5' & `ymean6' \\" _n
file write tablewrite "Clusters & `nclust1' & `nclust2' & `nclust3' && `nclust4' & `nclust5' & `nclust6' \\" _n
file write tablewrite "Observations & `nobs1' & `nobs2' & `nobs3' && `nobs4' & `nobs5' & `nobs6' \\" _n
file write tablewrite "[0.1em]" _n
file write tablewrite "\hline" _n
file write tablewrite "\vspace{-3mm}" _n
file write tablewrite "\\" _n
file write tablewrite "First-stage estimate &  " _n
file write tablewrite "$`beta7'$`stars7' & $`beta8'$`stars8' & $`beta9'$`stars9' && $`beta7'$`stars7' & $`beta8'$`stars8' & $`beta9'$`stars9' \\" _n
file write tablewrite "~~(standard error) & $(`se7')$ & $(`se8')$ & $(`se9')$ && $(`se7')$ & $(`se8')$ & $(`se9')$ \\" _n
file write tablewrite "[0.5em]"
file write tablewrite "First-stage \$F\$-statistic & `fstat1' & `fstat2' & `fstat3' && `fstat4' & `fstat5' & `fstat6' \\" _n
file write tablewrite "\hline" _n
file write tablewrite "\end{tabular}" _n
file write tablewrite "\vspace{-4mm}" _n
file write tablewrite "\caption*{\scriptsize Note. --- " _n
file write tablewrite "This table is identical to Table \ref*{tab:nss_2sls}, except that it adds state-specific linear time trends, " _n
file write tablewrite "which reduce our first-stage \$F\$-statistics for the Q1 and Q25 subsamples." _n
file write tablewrite "All regressions include: district fixed effects; year fixed effects; state-specific linear trends;  " _n
file write tablewrite "linear trends in state quartiles of 2005 household expenditures per capita; " _n 
file write tablewrite "and linear trends in national deciles of 2005 household expenditures per capita. " _n
file write tablewrite "Standard errors are clustered at the district level, collapsing to a " _n
file write tablewrite "single cluster for (i) districts that split in the 2001 Census, but which " _n
file write tablewrite "the 2000 NSS sampled based on 1991 district definitions; and (ii) the few cases " _n
file write tablewrite "where an RGGVY DPR included multiple districts." _n
file write tablewrite "The bottom three rows report the first-stage point estimates and standard errors, along with " _n
file write tablewrite "Kleibergen-Paap first-stage \$F\$-statistics. " _n
file write tablewrite "Significance: *** \$p < 0.01\$, ** \$p < 0.05\$, * \$p < 0.10\$." _n
file write tablewrite "}" _n
file write tablewrite "\end{table}" _n

file close tablewrite

}

********************************************************************************
********************************************************************************

** Table B11: NSS endogenous OLS DD, levels and logs
{
cap file close tablewrite
use "$results/nss_reg_results.dta", clear
keep if panel=="district-year collapsed"
keep if regs=="ols (endogenous 2nd stage)"
keep if inlist(yvar,"mth_pc_expE1","log_exp_30E1")
keep if inlist(ytag,"","_dec12","_dec30")
keep if ifs==""
keep if inlist(fes,"year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt")

gen c = .
replace c = 1 if yvar=="mth_pc_expE1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag==""
replace c = 2 if yvar=="mth_pc_expE1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_dec12"
replace c = 3 if yvar=="mth_pc_expE1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_dec30"
replace c = 4 if yvar=="log_exp_30E1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag==""
replace c = 5 if yvar=="log_exp_30E1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_dec12"
replace c = 6 if yvar=="log_exp_30E1" & fes=="year c.year#exp05_st_4ile c.year#exp05_ntl_10ile stdt" & ytag=="_dec30"
assert c!=.	
sort c

forvalues c = 1/3 {
		
	local beta`c' = string(beta[`c'],"%9.1f")
	local se`c' = string(se[`c'],"%9.1f")
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if  pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}
	
	local lci`c' = string(ci95_lo[`c'],"%9.1f")
	local uci`c' = string(ci95_hi[`c'],"%9.1f")
	local ymean`c' = string(ymean_pooled[`c'],"%9.1f")

	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']
	local fstat`c' = string(fstat[`c'],"%9.2f")
}	
	
forvalues c = 4/6 {

	local beta`c' = string(beta[`c'],"%9.3f")
	local se`c' = string(se[`c'],"%9.3f")
	if pvalue[`c'] <= 0.01 {
		local stars`c' = "$^{***}$"
	}
	else if  pvalue[`c'] <= 0.05 {
		local stars`c' = "$^{**}$"
	}
	else if pvalue[`c'] <= 0.10 {
		local stars`c' = "$^{*}$"
	}
	else {
		local stars`c' = ""
	}

	local lci`c' = string(ci95_lo[`c'],"%9.3f")
	local uci`c' = string(ci95_hi[`c'],"%9.3f")
	local ymean`c' = string(ymean_pooled[`c'],"%9.3f")

	local nobs`c' = nobs[`c']
	local nclust`c' = nclust[`c']
	local fstat`c' = string(fstat[`c'],"%9.2f")
}
	

   // MAKE TABLE
file open tablewrite using "$textab/table_nss_endog_ols.tex", write text replace
 
file write tablewrite "\begin{table}[h!]\centering" _n
file write tablewrite "\caption{District-level DD household consumption expenditures, without instrumenting}" _n
file write tablewrite "\label{tab:nss_endog_ols}" _n
file write tablewrite "\vspace{-3mm}" _n
file write tablewrite "\small" _n
file write tablewrite "\begin{tabular}{lccccccccc}" _n
file write tablewrite "\hline" _n
file write tablewrite "& \multicolumn{7}{c}{Expenditure per capita (Rs/month)}  \\ " _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\cline{2-8}\\" _n
file write tablewrite "\vspace{-0.90cm}" _n
file write tablewrite "\\" _n
file write tablewrite "& \multicolumn{3}{c}{Levels} & " _n
file write tablewrite "& \multicolumn{3}{c}{Logs} \\" _n
file write tablewrite "& (1) & (2) & (3) && (4) & (5) & (6) \\" _n
file write tablewrite "% \vspace{-0.40cm}" _n
file write tablewrite "% \\" _n
file write tablewrite "\cline{2-4} \cline{6-8}" _n
file write tablewrite "\vspace{-0.20cm}" _n
file write tablewrite "\\" _n
file write tablewrite "\$ \mathbf{1}\big[\text{HH consumes any elec}\big]~~ \$ & " _n
file write tablewrite "$`beta1'$`stars1' & $`beta2'$`stars2' & $`beta3'$`stars3' && $`beta4'$`stars4' & $`beta5'$`stars5' & $`beta6'$`stars6' \\" _n
file write tablewrite "& $(`se1')$ & $(`se2')$ & $(`se3')$ && $(`se4')$ & $(`se5')$ & $(`se6')$ \\" _n
file write tablewrite "[0.8em]" _n
file write tablewrite "95\% confidence & \$[`lci1'\$, & \$[`lci2'\$, & \$[`lci3'\$, && \$[`lci4'\$, & \$[`lci5'\$, & \$[`lci6'\$, \\" _n 
file write tablewrite "                & \$~`uci1']\$  & \$~`uci2']\$  & \$~`uci3']\$  && \$~`uci4']\$  & \$~`uci5']\$  & \$~`uci6']\$  \\ " _n 
file write tablewrite "[0.5em]" _n
file write tablewrite "Village weight quintiles & Pooled & 1 & 2--5 && Pooled & 1 & 2--5 \\" _n
file write tablewrite "[0.5em]" _n
file write tablewrite "Mean of dep var & `ymean1' & `ymean2' & `ymean3' && `ymean4' & `ymean5' & `ymean6' \\" _n
file write tablewrite "Clusters & `nclust1' & `nclust2' & `nclust3' && `nclust4' & `nclust5' & `nclust6' \\" _n
file write tablewrite "Observations & `nobs1' & `nobs2' & `nobs3' && `nobs4' & `nobs5' & `nobs6' \\" _n
file write tablewrite "\hline" _n
file write tablewrite "\end{tabular}" _n
file write tablewrite "\vspace{-4mm}" _n
file write tablewrite "\caption*{\scriptsize Note. --- Regressions are identical to those in " _n
file write tablewrite "Table \ref*{tab:nss_2sls}, except that estimate (endogenous) OLS models rather than instrumenting " _n
file write tablewrite "with the interaction \$\mathbf{1}\big[\text{10th-Plan district}\big] \times \mathbf{1}\big[2010\big]\$. " _n 
file write tablewrite "All regressions include: district fixed effects; year fixed effects;  " _n
file write tablewrite "linear trends in state quartiles of 2005 household expenditures per capita; " _n 
file write tablewrite "and linear trends in national deciles of 2005 household expenditures per capita. " _n
file write tablewrite "Standard errors are clustered at the district level, collapsing to a " _n
file write tablewrite "single cluster for (i) districts that split in the 2001 Census, but which " _n
file write tablewrite "the 2000 NSS sampled based on 1991 district definitions; and (ii) the few cases " _n
file write tablewrite "where an RGGVY DPR included multiple districts." _n
file write tablewrite "Significance: *** \$p < 0.01\$, ** \$p < 0.05\$, * \$p < 0.10\$." _n
file write tablewrite "}" _n
file write tablewrite "\end{table}" _n

file close tablewrite

}

********************************************************************************
********************************************************************************
