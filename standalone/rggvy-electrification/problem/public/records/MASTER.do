
************************
**** MASTER DO FILE ****
************************

* Path to folder containing all code
global path_code = "[YOUR PATH HERE]/code"

* File to set all paths to datasets
do "$path_code/PATHS.do"

* Multiple scripts use the function "unique" (-ssc install unique-)

******************************************
*** BUILD FILES starting from raw data ***
******************************************

* B1. Build Census datasets

	* B1.1. 2001 Primary Census Abstract
	do "$path_code/build/build_census_pca01.do"
		// input: "$pca/pca_census01_india.dta"
		// outputs: "$pca/pca_census01.dta", "$pca/pca_census01_names.dta"

	* B1.2. 2001-2011 Census concordance (for linking villages across Census years)
	do "$path_code/build/build_census_concordance.do"
		// inputs: "$conc/Rdir_2001_MDDS_*.csv"
		// outputs: "$conc/census_code_matches.dta", "$conc/census_code_matches_names.dta"

	* B1.3. 2011 Primary Census Abstract
	do "$path_code/build/build_census_pca11.do"
		// inputs: "$pca/pca_census11_india.dta", "$conc/census_code_matches_names.dta"
		// outputs: "$pca/pca_census11.dta", "$pca/pca_census11_names.dta"
		
	* B1.4. 1991 Primary Census Abstract (district level) 
	do "$path_code/build/build_census_pca91.do"
		// inputs: "$pca/pca_census91_st_dist.dta", "$pca/pca_census01_names.dta"
		// output: "$pca/pca_census91.dta"
				
	* B1.5. 2001 Village Directory	
	do "$path_code/build/build_census_vd01.do"
		// inputs: "$vd01/All/*.csv"
		// outputs: "$vd01/vd_2001.dta", "$vd01/vd_2001_names.dta"
		
	* B1.6. 2011 Village Directory
	do "$path_code/build/build_census_vd11.do"
		// inputs: "$vd11/raw village xlsx/*.xlsx"
		// outputs: "$vd11/vd_2011.dta", "$vd11/vd_2011_names.dta"

	* B1.7. 2001 Houselisting Primary Census Abstract (block level)	
	do "$path_code/build/build_census_hpca01.do"
		// inputs: "$hpca01/*/*.xls"
		// output: "$hpca01/hpca01_blockwise.dta"

	* B1.8. 2011 Houselisting Primary Census Abstract	
	do "$path_code/build/build_census_hpca11.do"
		// inputs: "$hpca11/python scraped csvs/*.csv"
		// output: "$hpca01/hpca11.dta"
		

* B2. Build nightlights datasets
do "$path_code/build/build_nightlights.do"
	// inputs: "$nl/nightlights_avg_vis/[state]/*.xls", "$nl/nightlights_stable/[state]/*.xls", 
	//         "$nl/nightlights_x_pct/[state]/*.xls" 
	// outputs: "$nl/nightlights_outcomes_avg_vis.dta", "$nl/nightlights_outcomes_stable.dta", 
	//          "$nl/nightlights_outcomes_x_pct.dta"		

	// NOTE: this step starts with village-level nightlights data that have been extracted
	// from satellite images using ArcGIS. See the README file for instructions on how to 
	// download the images and extract nightlights summary statistics for each village	
		
	
* B3. Build RGGVY datasets

	* B3.1. Village-level RGGVY data
	do "$path_code/build/build_rggvy_microdata.do"
		// inputs: "$rggvy/rggvy_combined_master.dta", "$loh/*.xls", 
		//         "$conc/census_code_matches_names.dta"
		// outputs: "$rggvy/rggvy_master_names.dta", "$rggvy/rggvy_list_of_habs.dta", 
		//          "$loh/rggvy_list_of_habs_names.dta"
	
	* B3.2. District-level RGGVY data
	do "$path_code/build/build_rggvy_districts.do"
		// inputs: "$rggvy/rggvy district-wise progress reports.csv", "$pca/pca_census01_names.dta", 
		//         "$pca/pca_census11_names.dta", "$pca/pca_census01_india.dta", 
		//         "$nl/nightlights_outcomes_avg_vis.dta"
		// outputs: "$rggvy/rggvy_district_progress_X_XI_totals.dta", "$rggvy/rggvy_district_progress_X_XI.dta", 
		//          "$rggvy/rggvy_district_progress_X_XI_processed.dta", "$rggvy/rggvy_districts_for_map.dta"


* B4. Build Socio Economic and Caste Census (SECC) datasets
do "$path_code/build/build_secc.do"
	// inputs: "$secc_raw/*", "$path_code/build/build_secc_clean.do"
	// outputs: "$secc/secc_dtas/st*/secc_indiv_rural_st*_dt*_*.dta"


* B5. Build NSS datasets
do "$path_code/build/build_nss.do"
   // inputs: "$nss/raw/multipliers/Dictionaries/mlt_61_1.dic", "$nss/raw/multipliers/Dictionaries/mlt_66_1.dic",
   //         "$nss/raw/multipliers/61/Multipliers(already posted onto data)/MULTALLS1.TXT", 
   //         "$nss/raw/multipliers/66_1/Multiplier ( already posted onto data)/amlt661.TXT",
   //         "$nss/raw/55th_round_1999_00/Data/*", "$nss/raw/61st_round_2004_05/Data/*",
   //         "$nss/raw/66th_round_2009_10_type1/Data/*"
   // outputs: "$nss/Final/nss_hhlevel_clean_withframepops.dta"
   	

* B6. Build elevation dataset 
do "$path_code/build/build_elevation.do"
	// inputs: "$path/data/other spatial data/SRTM-elevation/raw xls/*elevation.xls", 
	//         "$path/data/other spatial data/SRTM-elevation/raw xls/*extra.xls"
	// output: "$path/data/village gis maps/elev_stata_all.dta"
	
	// NOTE: this step starts with village-level gradient data that have been extracted
	// from satellite images using ArcGIS. See the README file for instructions on how to 
	// extract elevation summary statistics for each village.	


* B7. Build Economic Census datasets
do "$path_code/build/build_economic_census.do"
    // inputs: "$ec/1990/raw/*", "$ec/1998/raw/*", "$ec/2005/raw/*", "$ec/2013/raw/*",
	//         "$ec/1990/dictionaries/*", "$ec/1998/dictionaries/*", 
	//         "$ec/2005/dictionaries/*", "$ec/2013/dictionaries/*", "$ec/2013/Docs/NIC2008_3_DIGIT_CODE_LIST.xls",
	//         "$pca/pca_census01_names.dta", "$pca/pca_census11_names.dta"
	// outputs: "$ec/village_nic1990.dta", "$ec/village_nic1998.dta", 
	//          "$ec/village_nic2005.dta", "$ec/village_nic2013.dta",  
	
	
* B8. Build village distances from opposite-plan districts
do "$path_code/build/build_spatial_dd_dist.do"
	// inputs: "$path/data/village gis maps/village shapefiles/points_with_dd_dists/*.txt",
	//         "$rggvy/rggvy_district_progress_X_XI_processed.dta"
	// output: "$path/data/village gis maps/villages_with_distances_all.dta"

	// NOTE: this step starts with village-level distance that have been calculated in ArcGIS
	// by merging MLInfoMaps village and district polygons with RGGVY district-wise Plan assignments. 
	// See the README file for instructions on how to construct these village-specific distances.

	
	
******************************************************************
*** MERGE FILES to construct datasets for econometric analysis ***
******************************************************************

* M1. Merge together 6 Census datasets to create two-wave (wide) Census panel at the village level
do "$path_code/merge/merge_census_panel.do"
	// inputs: "$pca/pca_census01.dta", "$hpca01/hpca01_blockwise.dta", "$vd01/vd_2001.dta", 
	//         "$pca/pca_census11.dta", "$hpca11/hpca11.dta", "$vd11/vd_2011.dta"
	// output: "$panel/census_panel_2001_2011.dta"

	
* M2. Fuzzy merge between Census villages and villages in the 2003+2009 Habitation Census
do "$path_code/merge/merge_habitation.do"
	// inputs: "$pca/pca_census01_names.dta", "$vd01/vd_2001_names.dta", "$pca/pca_census11_names.dta", 
	//         "$conc/census_code_matches_names.dta", "$rggvy/rggvy_master_names.dta", 
	//         "$loh/rggvy_list_of_habs_names.dta", "$rggvy/rggvy_district_progress_X_XI.dta", 
	//         "$hab3/final/final.csv", "$hab9/BASIC_HABITATION_INFORMATION_AS_ON_1_APR_09.csv", 
	//         "$path_code/merge/merge_habitation_fuzzy_2003.do", "$path_code/merge/merge_habitation_fuzzy_2009.do", 
	//         "$path_code/merge/masala_merge_lp_server.do", "$path_code/merge/lev.py"
	// output: "$panel/pca_2001_names_hab_merge_final.dta"

	// NOTE: we executed this computationally intensive habitation merge in steps, using an external server, however
	// for the purposes of this replication archive, we have linearized the file paths so that it will be internally 
	// consistent within our data and code folder structures. To operationalize this step, we would encourage future 
	// researchers to rejigger the file paths within the three auxiliary .do files (rather than pass through globals).
	
	// 'masala_merge_lp_server.do' is a slightly modified version of Asher and Novosad's 'masala_merge.do', which calls
	// uses Stata to call the python script 'lev.py' in the command line. We adapted this script in July 2015. The 
	// updated code lives here: https://github.com/paulnov/masala-merge

	// The fuzzy matching Steps 1-4 (upstream from masala_merge) use the 20100118 distribution of the 'reclink' Stata module.

	
* M3. Merge together "full" panel datasets (i.e. Lights + Census + habitation merge)
do "$path_code/merge/merge_full_dataset.do"	
	// inputs: "$nl/nightlights_outcomes_avg_vis.dta", "$nl/nightlights_outcomes_stable.dta", 
	//         "$nl/nightlights_outcomes_x_pct.dta", "$nl/attrtables_all.dta", "$pca/pca_census91.dta",
	//         "$path/data/village gis maps/attrtables_lat_lon.dta", "$panel/census_panel_2001_2011.dta", 
	//         "$panel/pca_2001_names_hab_merge_final.dta", "$path_code/merge/merge_spatial_ngh_outcomes.do", 
	//         "$path/data/village gis maps/villages_with_distances_all.dta", "$path/data/village gis maps/elev_stata_all.dta", 
	// outputs: "$panel/panel_dataset_no_outcomes.dta", "$panel/panel_dataset_no_lights.dta", "$panel/panel_dataset_rd_sample.dta",
	//          "$panel/panel_dataset_full.dta", "$panel/panel_dataset_dd_91.dta", 
	//          "$panel/panel_dataset_dd.dta", "$panel/panel_dataset_dd_91dt.dta"
	
	// NOTE: these "full" panel dataset are the foundation, establish our cross-sectional unit as the 2001 Census village or the
	// 2001 district. The subsequent merge steps M4-M9 use this foundation to incorporate other datasets.
	
	// While original version of this paper used an RD window of 150-450 people, our analysis now uses 'rdrobust' to calculate an 
	// optimal bandwidth for each RD regression. Reflective of this change, this dataset creates several obsolete variables that 
	// direclty pertained to a 150-450-person RD window, which we no longer use in our analysis. The dataset 
	// "$panel/panel_dataset_rd_sample.dta" is likewise obsolete, since we no longer impose a bandwidth restriction *before*
	// feeding data into our RD estimation scripts.
	
	// The panel datasets with the 1991 district-level PCA are also obsolete; we no longer use them in our district-level DD analysis.
	
	// This step calls "$path_code/merge/merge_spatial_ngh_outcomes.do", which we no longer use in our analysis. It calculates 
	// average values of key village-level variables for neighboring villages within certain distance radii, and has a long run time.
	// It uses the 'geodist' Stata module.

	
* M4. Fuzzy merge between Census villages and villages in the 2011 SECC
do "$path_code/merge/merge_secc.do"	
	// inputs: "$pca/pca_census01_names.dta", "$vd01/vd_2001_names.dta", "$pca/pca_census11_names.dta", 
	//         "$vd11/vd_2011_all_raw.dta", "$secc/secc_dtas/st*/secc_indiv_rural_st*_dt*_*.dta",
	//         "$path_code/merge/masala_merge_lp_server.do"
	// outputs: "$secc/secc_dtas_indiv/st*/secc_pca_indiv_rural_st*_dt*.dta"
	
	// NOTE: this step uses the same 'masala_merge' algorithm (see notes above). Since this fuzzy merge is 
	// considerably less "fuzzy", it goes much faster here.
	

* M5. Consolidate and collapse SECC dataset
do "$path_code/merge/merge_secc_collapse.do"	
	// inputs: "$secc/secc_dtas_indiv/st*/*.dta"
	// output: "$panel/secc_pca_vill_all.dta"
	
	
* M6. Merge DISE schools data to Census villages
do "$path_code/merge/merge_schools.do"
    // inputs: "$pca/pca_census01_names.dta", "$vd01/vd_2001_names.dta", "$pca/pca_census11_names.dta"
	//         "$vd11/vd_2011_all_raw.dta", "$conc/census_code_matches_names.dta", "$panel/panel_dataset_no_lights.dta",
	//         "$vd11/vd_2011.dta", "$schools/school_village_codes_ALL_unique_new.dta", "$schools/dise_testscore_update_final.dta"
	//         "$path_code/merge/merge_schools_fuzzy.do", 
	//         "$path_code/merge/masala_merge_lp_server.do", "$path_code/merge/lev.py"
    // outputs: "$panel/pca_school_selected_panel_new.dta, "$panel/pca_school_selected_WIDE_new.dta",
	//          "$panel/pca_school_selected_schoollevel_panel_new.dta, "$panel/pca_school_selected_schoollevel_WIDE_new.dta"

	
* M7. Merge in raw SHRUG data, at the village level
do "$path_code/merge/merge_shrug.do"	
	// inputs: "$shrug/shrug-v1.4.samosa-keys-dta/shrug_pc01r_key.dta", 
	//         "$shrug/shrug-v1.4.samosa-ancillary-dta/shrug_ancillary.dta", "$panel/panel_dataset_full.dta"
	// output: "$shrug/shrug_secc.dta"	
	

* M8: Construct collapsed and uncollapsed NSS datasets for analysis	
do "$path_code/merge/merge_nss_panel.do"	
	// inputs: "$nss/Final/nss_hhlevel_clean_withframepops.dta", "$pca/pca_census91.dta",
	//         "$nss/INDCPIALLAINMEI.xls", "$panel/panel_dataset_no_outcomes.dta", "$pca/pca_census91_st_dist.dta",
	//         "$panel/panel_dataset_dd.dta", 
	// outputs: "$panel/panel_dataset_dd_nss.dta", "$panel/panel_dataset_dd_nss_uncollapsed.dta"

	
* M9: Merge Economic Census data to Census villages / SHRUG
do "$path_code/merge/merge_economic_census.do"
	// inputs: "$ec/village_nic1990.dta", "$ec/village_nic1998.dta", 
	//          "$ec/village_nic2005.dta", "$ec/village_nic2013.dta",
	//          "$shrug/shrug-v1.4.samosa-keys-dta/shrug_ec`ec_yr'r_key.dta",
	//          "$shrug/shrug-v1.4.samosa-keys-dta/shrug_ec`ec_yr'r_key_wdist_subdist_ids.dta",
	//          "$shrug/shrug_pca01_xwalk.dta", "$panel/panel_dataset_full.dta",
	// output:  "$panel/ec_shrid_pc01_panel.dta"
	
	// This do file uses the 'gtools' and 'ftools' Stata modules.


***********************************************************************************************
*** ANALYZE FILES: regressions, benefit/cost calculations, and placebo/randomization tests  ***
***********************************************************************************************

	// RD regressions use the 20200406 distribution of the 'rdrobust' Stata module.
	// DD regressions use the 20191118 distribution of the 'reghdfe' Stata module,
	//                    the 20180915 distribtuion of the 'ivreghdfe' Stata module,
	//                    the 20200626 distribution of the 'ivreg2' Stata module,
	//                    the 20191118 distribution of the 'ftools' Stata module,
	//                    the 20200929 distribution of the 'ranktest' Stata module,
	//                and the dropmiss function in the 'dm89_2' Stata module.
	
* A1. First-stage RD regressions (and sensitivities)
do "$path_code/analyze/RDROBUST_fs_vdelec.do"
do "$path_code/analyze/RDROBUST_fs_lights.do"
	// input: "$panel/panel_dataset_full.dta"
	// outputs: "$results/RDROBUST_fs_vdelec.dta", "$results/RDROBUST_fs_lights.dta",
	//			"$results/"RDROBUST plots fs vdelec/*", "$results/"RDROBUST plots fs lights/*",
	//          "$sens/RDROBUST_placebo_test_vdelec.dta", "$sens/RDROBUST_placebo_test_lights.dta"

	
* A2. Reduced-form RD regressions (and sensitivities)
do "$path_code/analyze/RDROBUST_rf_census_outcomes.do"
do "$path_code/analyze/RDROBUST_rf_ec_outcomes.do"
do "$path_code/analyze/RDROBUST_rf_schools_outcomes.do"
do "$path_code/analyze/RDROBUST_rf_secc_outcomes.do"
do "$path_code/analyze/RDROBUST_rf_shrug_outcomes.do"
	// inputs: "$panel/panel_dataset_full.dta", "$hpca11/hpca11.dta", "$panel/ec_shrid_pc01_panel.dta", 
	//         "$vd11/vd_2011.dta", "$panel/pca_school_selected_WIDE_new.dta", 
	//         "$panel/secc_pca_vill_all.dta", "$shrug/shrug_secc.dta",
	//         "$path_code/analyze/RDROBUST_rf_outcomes_graphspecs.do"
	// outputs: "$results/RDROBUST_outcomes_rf_census.dta", "$results/RDROBUST_outcomes_rf_ec.dta", 
	//          "$results/RDROBUST_outcomes_rf_schools.dta", "$results/RDROBUST_outcomes_rf_secc.dta", 
	//          "$results/RDROBUST_outcomes_rf_shrug.dta",
	//          "$results/RDROBUST plots rf outcomes preferred/*", "$results/RDROBUST plots rf outcomes popmismatch", 
	//          "$results/RDROBUST plots rf outcomes lights outliers", "$results/RDROBUST plots rf outcomes epa kernel", 
	//          "$results/RDROBUST plots rf outcomes uni kernel", "$results/RDROBUST plots rf outcomes no lights controls", 
	//          "$results/RDROBUST plots rf outcomes no FEs", "$results/RDROBUST plots rf outcomes district FEs", 
	//          "$results/RDROBUST plots rf outcomes nncluster by district", "$results/RDROBUST plots rf outcomes cluster by district", 
	//          "$results/RDROBUST plots rf outcomes CERRD bandwidth", "$results/RDROBUST plots rf outcomes no 2005 controls"

	
* A3. Fuzzy RD regressions (and sensitivities)
do "$path_code/analyze/RDROBUST_fuzzy_census_outcomes.do"
do "$path_code/analyze/RDROBUST_fuzzy_ec_outcomes.do"
do "$path_code/analyze/RDROBUST_fuzzy_schools_outcomes.do"
do "$path_code/analyze/RDROBUST_fuzzy_secc_outcomes.do"
do "$path_code/analyze/RDROBUST_fuzzy_shrug_outcomes.do"
	// inputs: "$panel/panel_dataset_full.dta", "$hpca11/hpca11.dta", "$panel/ec_shrid_pc01_panel.dta", 
	//         "$vd11/vd_2011.dta", "$panel/pca_school_selected_WIDE_new.dta", 
	//         "$panel/secc_pca_vill_all.dta", "$shrug/shrug_secc.dta",
	// outputs: "$results/RDROBUST_outcomes_fuzzy_census.dta", "$results/RDROBUST_outcomes_fuzzy_ec.dta", 
	//          "$results/RDROBUST_outcomes_fuzzy_schools.dta", "$results/RDROBUST_outcomes_fuzzy_secc.dta", 
	//          "$results/RDROBUST_outcomes_fuzzy_shrug.dta"


* A4. First-stage RD regressions, heterogeneous by impelmentation intensity (and sensitivities)
do "$path_code/analyze/RDROBUST_fs_vdelec_dpr.do"
do "$path_code/analyze/RDROBUST_fs_lights_dpr.do"
	// inputs: "$panel/panel_dataset_full.dta", "$rggvy/rggvy_district_progress_X_XI_processed.dta"
	// outputs: "$results/RDROBUST_fs_vdelec.dta", "$results/RDROBUST_fs_lights.dta",
	//			"$results/"RDROBUST plots fs vdelec DPR/*", "$results/"RDROBUST plots fs lights DPR/*"

	
* A5. Reduced-form RD regressions, heterogeneous by impelmentation intensity (and sensitivities)
do "$path_code/analyze/RDROBUST_rf_census_outcomes_dpr.do"
do "$path_code/analyze/RDROBUST_rf_ec_outcomes_dpr.do"
do "$path_code/analyze/RDROBUST_rf_schools_outcomes_dpr.do"
do "$path_code/analyze/RDROBUST_rf_secc_outcomes_dpr.do"
do "$path_code/analyze/RDROBUST_rf_shrug_outcomes_dpr.do"
	// inputs: "$panel/panel_dataset_full.dta", "$hpca11/hpca11.dta", "$panel/ec_shrid_pc01_panel.dta", 
	//         "$vd11/vd_2011.dta", "$panel/pca_school_selected_WIDE_new.dta", 
	//         "$panel/secc_pca_vill_all.dta", "$shrug/shrug_secc.dta",
	//         "$path_code/analyze/RDROBUST_rf_outcomes_graphspecs.do",
	//         "$rggvy/rggvy_district_progress_X_XI_processed.dta"
	// outputs: "$results/RDROBUST_outcomes_rf_census_dpr.dta", "$results/RDROBUST_outcomes_rf_ec_dpr.dta", 
	//          "$results/RDROBUST_outcomes_rf_schools_dpr.dta", "$results/RDROBUST_outcomes_rf_secc_dpr.dta", 
	//          "$results/RDROBUST_outcomes_rf_shrug_dpr.dta",
	//          "$results/RDROBUST plots rf outcomes preferred/*", "$results/RDROBUST plots rf outcomes epa kernel", 
	//          "$results/RDROBUST plots rf outcomes uni kernel", "$results/RDROBUST plots rf outcomes CERRD bandwidth"

	
* A6. Fuzzy RD regressions, heterogeneous by impelmentation intensity (and sensitivities)
do "$path_code/analyze/RDROBUST_fuzzy_census_outcomes_dpr.do"
do "$path_code/analyze/RDROBUST_fuzzy_ec_outcomes_dpr.do"
do "$path_code/analyze/RDROBUST_fuzzy_schools_outcomes_dpr.do"
do "$path_code/analyze/RDROBUST_fuzzy_secc_outcomes_dpr.do"
do "$path_code/analyze/RDROBUST_fuzzy_shrug_outcomes_dpr.do"
	// inputs: "$panel/panel_dataset_full.dta", "$hpca11/hpca11.dta", "$panel/ec_shrid_pc01_panel.dta", 
	//         "$vd11/vd_2011.dta", "$panel/pca_school_selected_WIDE_new.dta", 
	//         "$panel/secc_pca_vill_all.dta", "$shrug/shrug_secc.dta",
	//         "$rggvy/rggvy_district_progress_X_XI_processed.dta"
	// outputs: "$results/RDROBUST_outcomes_fuzzy_census_dpr.dta", "$results/RDROBUST_outcomes_fuzzy_ec_dpr.dta", 
	//          "$results/RDROBUST_outcomes_fuzzy_schools_dpr.dta", "$results/RDROBUST_outcomes_fuzzy_secc_dpr.dta", 
	//          "$results/RDROBUST_outcomes_fuzzy_shrug_dpr.dta"


* A7. First-stage RD regressions, heterogeneous by hours of power (and sensitivities)
do "$path_code/analyze/RDROBUST_fs_vdelec_hrs.do"
do "$path_code/analyze/RDROBUST_fs_lights_hrs.do"
	// input: "$panel/panel_dataset_full.dta"
	// outputs: "$results/RDROBUST_fs_vdelec.dta", "$results/RDROBUST_fs_lights.dta",
	//			"$results/"RDROBUST plots fs vdelec HRS/*", "$results/"RDROBUST plots fs lights HRS/*"

	
* A8. Reduced-form RD regressions, heterogeneous by hours of power (and sensitivities)
do "$path_code/analyze/RDROBUST_rf_census_outcomes_hrs.do"
do "$path_code/analyze/RDROBUST_rf_ec_outcomes_hrs.do"
do "$path_code/analyze/RDROBUST_rf_schools_outcomes_hrs.do"
do "$path_code/analyze/RDROBUST_rf_secc_outcomes_hrs.do"
do "$path_code/analyze/RDROBUST_rf_shrug_outcomes_hrs.do"
	// inputs: "$panel/panel_dataset_full.dta", "$hpca11/hpca11.dta", "$panel/ec_shrid_pc01_panel.dta", 
	//         "$vd11/vd_2011.dta", "$panel/pca_school_selected_WIDE_new.dta", 
	//         "$panel/secc_pca_vill_all.dta", "$shrug/shrug_secc.dta",
	//         "$path_code/analyze/RDROBUST_rf_outcomes_graphspecs.do"
	// outputs: "$results/RDROBUST_outcomes_rf_census_hrs.dta", "$results/RDROBUST_outcomes_rf_ec_hrs.dta", 
	//          "$results/RDROBUST_outcomes_rf_schools_hrs.dta", "$results/RDROBUST_outcomes_rf_secc_hrs.dta", 
	//          "$results/RDROBUST_outcomes_rf_shrug_hrs.dta",
	//          "$results/RDROBUST plots rf outcomes preferred/*", "$results/RDROBUST plots rf outcomes epa kernel", 
	//          "$results/RDROBUST plots rf outcomes uni kernel", "$results/RDROBUST plots rf outcomes CERRD bandwidth"

	
* A9. Fuzzy RD regressions, heterogeneous by hours of power (and sensitivities)
do "$path_code/analyze/RDROBUST_fuzzy_census_outcomes_hrs.do"
do "$path_code/analyze/RDROBUST_fuzzy_ec_outcomes_hrs.do"
do "$path_code/analyze/RDROBUST_fuzzy_schools_outcomes_hrs.do"
do "$path_code/analyze/RDROBUST_fuzzy_secc_outcomes_hrs.do"
do "$path_code/analyze/RDROBUST_fuzzy_shrug_outcomes_hrs.do"
	// inputs: "$panel/panel_dataset_full.dta", "$hpca11/hpca11.dta", "$panel/ec_shrid_pc01_panel.dta", 
	//         "$vd11/vd_2011.dta", "$panel/pca_school_selected_WIDE_new.dta", 
	//         "$panel/secc_pca_vill_all.dta", "$shrug/shrug_secc.dta",
	// outputs: "$results/RDROBUST_outcomes_fuzzy_census_hrs.dta", "$results/RDROBUST_outcomes_fuzzy_ec_hrs.dta", 
	//          "$results/RDROBUST_outcomes_fuzzy_schools_hrs.dta", "$results/RDROBUST_outcomes_fuzzy_secc_hrs.dta", 
	//          "$results/RDROBUST_outcomes_fuzzy_shrug_hrs.dta"

	
* A10. Reduced-form RD regressions, including states with bad/missing shapefiles (and sensitivities)
do "$path_code/analyze/RDROBUST_rf_census_outcomes_badshapefiles.do"
do "$path_code/analyze/RDROBUST_rf_ec_outcomes_badshapefiles.do"
do "$path_code/analyze/RDROBUST_rf_schools_outcomes_badshapefiles.do"
do "$path_code/analyze/RDROBUST_rf_secc_outcomes_badshapefiles.do"
do "$path_code/analyze/RDROBUST_rf_shrug_outcomes_badshapefiles.do"
	// inputs: "$panel/panel_dataset_full.dta", "$hpca11/hpca11.dta", "$panel/ec_shrid_pc01_panel.dta", 
	//         "$vd11/vd_2011.dta", "$panel/pca_school_selected_WIDE_new.dta", 
	//         "$panel/secc_pca_vill_all.dta", "$shrug/shrug_secc.dta",
	//         "$path_code/analyze/RDROBUST_rf_outcomes_graphspecs.do"
	// outputs: "$results/RDROBUST_outcomes_rf_census_badshapefiles.dta", "$results/RDROBUST_outcomes_rf_ec_badshapefiles.dta", 
	//          "$results/RDROBUST_outcomes_rf_schools_badshapefiles.dta", "$results/RDROBUST_outcomes_rf_secc_badshapefiles.dta", 
	//          "$results/RDROBUST_outcomes_rf_shrug_badshapefiles.dta",
	//          "$results/RDROBUST plots rf outcomes preferred/*", "$results/RDROBUST plots rf outcomes epa kernel", 
	//          "$results/RDROBUST plots rf outcomes uni kernel", "$results/RDROBUST plots rf outcomes CERRD bandwidth"

	
* A11. Covariate smooothness RD regressions
do "$path_code/analyze/RDROBUST_smoothness_census_2001.do"
	// inputs: "$panel/panel_dataset_full.dta", "$path_code/analyze/RDROBUST_rf_outcomes_graphspecs.do"
	// outputs: "$results/RDROBUST_smoothness_census.dta",
	//          "$results/RDROBUST plots rf outcomes preferred/*", "$results/RDROBUST plots rf outcomes popmismatch", 
	//          "$results/RDROBUST plots rf outcomes lights outliers", "$results/RDROBUST plots rf outcomes epa kernel", 
	//          "$results/RDROBUST plots rf outcomes uni kernel", "$results/RDROBUST plots rf outcomes no lights controls", 
	//          "$results/RDROBUST plots rf outcomes no FEs", "$results/RDROBUST plots rf outcomes district FEs", 
	//          "$results/RDROBUST plots rf outcomes nncluster by district", "$results/RDROBUST plots rf outcomes cluster by district", 
	//          "$results/RDROBUST plots rf outcomes CERRD bandwidth", "$results/RDROBUST plots rf outcomes no 2005 controls"

	
* A12. First-stage DD regressions (non-NSS), including difference-in-discontinuities
do "$path_code/analyze/DD_regs_lights.do"
do "$path_code/analyze/DD_regs_vdelec.do"
	// inputs: "$panel/panel_dataset_dd.dta", "$panel/panel_dataset_full.dta", "$panel/panel_dataset_dd_nss.dta", 
	//         "$rggvy/rggvy_district_progress_X_XI_processed.dta"
	// outputs: "$panel/panel_dataset_lights_allyears.dta" "$results/diff_in_disc_vdelec.dta", "$results/dd_vdelec_distlevel.dta",
	//          "$results/dd_vdelec_pooled.dta", "$results/dd_vdelec_popbins.dta", "$results/dd_results_lights_allyears.dta", 
	//          "$results/dd figs/event_study_lights_bothplans.eps", "$results/dd figs/event_study_lights_10thplan.eps", 
	//          "$results/dd figs/diff_in_disc_lights_dt_100.pdf", "$results/dd figs/diff_in_disc_lights_dt_150.pdf", 
	//          "$results/dd figs/diff_in_disc_lights_dt_100_hours.pdf", "$results/dd figs/diff_in_disc_lights_dt_150_hours.pdf"


* A13. Reduced-form DD regressions (non-NSS), including difference-in-discontinuities
do "$path_code/analyze/DD_regs_census.do"
do "$path_code/analyze/DD_regs_ec.do"
do "$path_code/analyze/DD_regs_schools.do"
	// inputs: "$panel/panel_dataset_dd.dta", "$panel/panel_dataset_lights_allyears.dta", "$panel/panel_dataset_full.dta", 
	//         "$panel/panel_dataset_dd_nss.dta", "$panel/ec_shrid_pc01_panel.dta", "$panel/panel_dataset_no_lights.dta",
	//         "$panel/pca_school_selected_panel_new.dta", "$rggvy/rggvy_district_progress_X_XI_processed.dta"
	// outputs: "$results/diff_in_disc_outcomes_census.dta", "$results/dd_outcomes_census_distlevel.dta", 
	//          "$results/dd_outcomes_census_pooled.dta", "$results/diff_in_disc_outcomes_ec.dta", 
	//          "$results/dd_results_outcomes_ec_4years.dta", "$results/diff_in_disc_outcomes_schools.dta", 
	//          "$results/dd_results_outcomes_dise_allyears.dta"


* A14. All NSS regressions 
do "$path_code/analyze/DD_regs_NSS.do"
	// inputs: "$panel/panel_dataset_dd_nss.dta", "$panel/panel_dataset_full.dta", 
	//         "$rggvy/rggvy_district_progress_X_XI_processed.dta", "$panel/panel_dataset_dd_nss_uncollapsed.dta"
	// outputs: "$results/nss_reg_results.dta"
	

* A15. Benefit-cost analysis
do "$path_code/analyze/ROI_calcs_expenditure.do"
do "$path_code/analyze/ROI_calcs_cs.do"
	// inputs: "$panel/panel_dataset_full.dta", "$nss/INDCPIALLAINMEI.xls", "$results/RDROBUST_outcomes_fuzzy_shrug.dta", 
	//         "$results/nss_reg_results.dta", "$panel/panel_dataset_dd_nss_uncollapsed.dta", "$panel/panel_dataset_no_lights.dta"
	// outputs: "$results/expenditure_sampling_distributions.pdf", "$results/roi_results_expenditure_bootstraps_full.dta", 
	//          "$results/roi_results_expenditure_bootstraps.dta", "$results/roi_results_cs_full.dta", 
	//          "$results/roi_results_cs.dta", "$results/roi_results_cs_irr.dta"


* A16. Placebo and randomization tests 
do "$path_code/analyze/PLACEBO_test_rdrobust_vdelec.do"
do "$path_code/analyze/PLACEBO_test_rdrobust_lights.do"
do "$path_code/analyze/RANDOMIZATION_test_dd_NSS.do"
	// inputs: "$sens/RDROBUST_placebo_test_vdelec.dta", "$sens/RDROBUST_placebo_test_lights.dta", 
	//         "$panel/panel_dataset_dd_nss.dta" 
	// outputs: "$sens/RDROBUST_placebo_test_vdelec_results.dta", "$sens/RDROBUST_placebo_test_lights_results.dta",
	//          "$sens/nss_dd_randomization_test.dta"
	
	

*****************************************************************************************
*** OUTPUT FILES, which generate all tables and figures in the main text and appendix ***
*****************************************************************************************

* O1. Generate all summary tables and figures
do "$path_code/outputs/outputs_summary.do"
	// inputs: "$hmerge/pca_2001_names_merges_all_matched3_processed.dta", "$hmerge/pca_2001_names_merges_all_matched9_processed.dta",
	//         "$nss/INDCPIALLAINMEI.xls", "$loh/rggvy_list_of_habs_names.dta", "$other/elec_rate.csv", "$other/population.csv", 
	//         "$other/gdp_pc_2010.csv", "$panel/ec_shrid_pc01_panel.dta", "$panel/census_panel_2001_2011.dta", 
	//         "$panel/panel_dataset_dd_nss.dta", "$panel/panel_dataset_dd_nss_uncollapsed.dta", "$panel/panel_dataset_full.dta",
	//         "$panel/panel_dataset_no_lights.dta", "$panel/panel_dataset_no_outcomes.dta", "$panel/pca_2001_names_hab_merge_final.dta",
	//         "$panel/pca_school_selected_WIDE_new.dta", "$panel/secc_pca_vill_all.dta", "$pca/pca_census01_names.dta", 
	//         "$pca/pca_census11.dta", "$pca/pca_census11_names.dta", "$results/nss_reg_results.dta", 
	//         "$rggvy/rggvy_district_progress_X_XI_processed.dta", "$rggvy/rggvy_covered_master.dta",	
	//         "$rggvy/rggvy_completed_master.dta", "$shrug/shrug_secc.dta",
	//         "$texfig/rggvy_district_map_all_hash_grayscale_wide.pdf", "$texfig/nightlights_zoomed2_FINAL.pdf" 
	
	// Figure 1:  "$texfig/figure_gdp_unelec.eps", "$texfig/figure_gdp_unelec.tex"
	// Figure 2:  "$texfig/figure_rggvy_districts.tex" 
	// Figure 3:  "$texfig/figure_pop_hist_150_450.eps", "$texfig/figure_pop_hist_wide.eps", "$texfig/figure_pop_hist.tex"
	// Table 1:   "$textab/table_sumstats.tex"
	// Figure A6: "$texfig/figure_hist_rggvy_intensity.pdf", "$texfig/figure_hist_rggvy_intensity.tex"
	// Figure A8: "$texfig/figure_hist_hours.pdf", "$texfig/figure_hist_hours.tex"
	// Table C1:  "$textab/table_rggvy_irreg.tex",
	// Table C2:  "$textab/table_summary_stats_rggvy.tex"
	// Table C3:  "$textab/table_state_corr.tex"
	// Figure C1: "$texfig/figure_lights_zoomed.tex"
	// Table C4:  "$textab/table_hab_merge.tex"
	// Figure C2: "$texfig/figure_hab_merge_hist.pdf", "$texfig/figure_hab_merge_hist.tex"
	// Figure C3: "$texfig/figure_secc_merge_hist.pdf", "$texfig/figure_secc_merge_hist.tex"
	// Figure C4: "$texfig/figure_ec_merge_hist.pdf", "$texfig/figure_ec_merge_hist.tex"
	// Figure C5: "$texfig/figure_schools_merge_hist.pdf", "$texfig/figure_schools_merge_hist.tex"	
	// Table C5:  "$textab/table_village_counts.tex"
	// Figure C6: "$texfig/figure_nss_weights_hist_2005.pdf", "$texfig/figure_nss_weights_hist_2010.pdf", 
	//            "$texfig/figure_nss_weights_kdens_2005.pdf", "$texfig/figure_nss_weights_kdens_2010.pdf", 
	//            "$texfig/figure_nss_weights_dist.tex"

	
* O2. Generate all first-stage Census electricitiy tables and figures
do "$path_code/outputs/outputs_vdelec.do"
	// inputs: "$results/dd_vdelec_pooled.dta", "$results/dd_vdelec_distlevel.dta", "$results/dd_vdelec_popbins.dta",
	//         "$results/diff_in_disc_vdelec.dta", "$results/RDROBUST_fs_vdelec.dta", "$results/RDROBUST_fs_vdelec_dpr.dta",
	//         "$results/RDROBUST plots fs vdelec/vd_pwr_d_com_11_fs_preferred_inreg_10.pdf",
	//         "$results/RDROBUST plots fs vdelec/vd_pwr_h_com_11_fs_preferred_inreg_10.pdf",
	//         "$results/RDROBUST plots fs vdelec/vd_pwr_d_all_11_fs_preferred_inreg_10.pdf",
	//         "$results/RDROBUST plots fs vdelec/vd_pwr_h_all_11_fs_preferred_inreg_10.pdf",
	//         "$results/RDROBUST plots fs vdelec/vd_pwr_d_dom_11_fs_preferred_inreg_10.pdf",
	//         "$results/RDROBUST plots fs vdelec/vd_pwr_h_dom_11_fs_preferred_inreg_10.pdf",
	//         "$results/RDROBUST plots fs vdelec/vd_pwr_d_agr_11_fs_preferred_inreg_10.pdf",
	//         "$results/RDROBUST plots fs vdelec/vd_pwr_h_agr_11_fs_preferred_inreg_10.pdf",
	//         "$sens/RDROBUST_placebo_test_vdelec_results.dta", 
	
	// Table 2:   "$textab/table_rd_vdelec.tex"
	// Figure 4:  "$texfig/vd_pwr_d_com_11_fs_preferred_inreg_10.pdf", "$texfig/vd_pwr_h_com_11_fs_preferred_inreg_10.pdf", 
	//            "$texfig/vd_pwr_d_all_11_fs_preferred_inreg_10.pdf", "$texfig/vd_pwr_h_all_11_fs_preferred_inreg_10.pdf",
	//            "$texfig/figure_rd_vdelec.tex"
	// Table A1:  "$textab/table_diff_in_disc_vdelec.tex"
	// Table A2:  "$textab/table_dd_vdelec.tex"
	// Table A3:  "$textab/table_dd_dist_vdelec.tex"
	// Figure A2: "$texfig/figure_dd_vdelec_by_popbin.pdf", "$texfig/figure_dd_vdelec_by_popbin.tex"
	// Figure A4: "$texfig/vd_pwr_d_dom_11_fs_preferred_inreg_10.pdf", "$texfig/vd_pwr_h_dom_11_fs_preferred_inreg_10.pdf",
	//            "$texfig/vd_pwr_d_agr_11_fs_preferred_inreg_10.pdf", "$texfig/vd_pwr_h_agr_11_fs_preferred_inreg_10.pdf",
	//            "$texfig/figure_rd_vdelec_bonus.tex"
	// Table A12: "$textab/table_rd_vdelec_hi_intens.tex"
	// Table A18: "$textab/table_diff_in_disc_vdelec_hours.tex"
	// Figure B1: "$texfig/rd_vdelec_coeffs_sens_dcom.pdf", "$texfig/rd_vdelec_coeffs_sens_hcom.pdf", 
	//            "$texfig/rd_vdelec_coeffs_sens_dall.pdf", "$texfig/figure_rd_vdelec_sens.tex"
	// Figure B3: "$texfig/rd_vdelec_coeffs_falsif_dcom.pdf", "$texfig/rd_vdelec_coeffs_falsif_dall.pdf",
	//            "$texfig/rd_vdelec_coeffs_falsif_hcom.pdf", "$texfig/figure_rd_vdelec_falsif.tex"
	// Figure B5: "$texfig/placebo_test_vdelec_rdrobust_dall.pdf", "$texfig/placebo_test_vdelec_rdrobust_dcom.pdf",
	//            "$texfig/placebo_test_vdelec_rdrobust_hcom.pdf", "$texfig/figure_rd_first_stage_placebo.tex"
	
	
* O3. Generate all first-stage nighttime brightness tables and figures
do "$path_code/outputs/outputs_lights.do"
	// inputs: "$results/dd_results_lights_allyears.dta", 
	//         "$results/dd figs/diff_in_disc_lights_dt_100.pdf", "$results/dd figs/diff_in_disc_lights_dt_150.pdf",
    //         "$results/dd figs/diff_in_disc_lights_dt_100_hours.pdf", "$results/dd figs/diff_in_disc_lights_dt_150_hours.pdf",
	//         "$results/dd figs/event_study_lights_10thplan.eps", "$results/dd figs/event_study_lights_bothplans.eps",
	//         "$results/RDROBUST_fs_lights.dta", "$results/RDROBUST_fs_lights_dpr.dta",
	//		   "$results/RDROBUST plots fs lights/lights_fs_preferred_2002_wide_10.pdf",
	//		   "$results/RDROBUST plots fs lights/lights_fs_preferred_2003_wide_10.pdf",
	//		   "$results/RDROBUST plots fs lights/lights_fs_preferred_2004_wide_10.pdf",
	//		   "$results/RDROBUST plots fs lights/lights_fs_preferred_2005_wide_10.pdf",
	//		   "$results/RDROBUST plots fs lights/lights_fs_preferred_2006_wide_10.pdf",
	//		   "$results/RDROBUST plots fs lights/lights_fs_preferred_2007_wide_10.pdf",
	//		   "$results/RDROBUST plots fs lights/lights_fs_preferred_2008_wide_10.pdf",
	//		   "$results/RDROBUST plots fs lights/lights_fs_preferred_2009_wide_10.pdf",
	//		   "$results/RDROBUST plots fs lights/lights_fs_preferred_2010_wide_10.pdf",
	//		   "$results/RDROBUST plots fs lights/lights_fs_preferred_2011_wide_10.pdf",
	//		   "$results/RDROBUST plots fs lights/lights_fs_preferred_2012_wide_10.pdf",
	//		   "$sens/RDROBUST_placebo_test_lights_results.dta"
		
	// Figure 5:  "$texfig/rd_lights_coeffs_by_year.eps", "$texfig/figure_rd_lights_by_year.tex"
	// Figure 6:  "$texfig/event_study_lights_10thplan.eps", "$texfig/event_study_lights_bothplans.eps",
	//            "$texfig/figure_event_study_lights.tex"
	// Figure A1: "$texfig/diff_in_disc_lights_dt_150.pdf"," $texfig/diff_in_disc_lights_dt_100.pdf", "$texfig/figure_diff_in_disc_lights.tex"
	// Table A4:  "$textab/table_dd_village_lights.tex"
	// Figure A3: "$texfig/dd_lights_by_popbin.pdf", "$texfig/figure_dd_lights_by_popbin.tex"
	// Table A10: "$textab/table_rd_lights.tex"
	// Figure A5: "$texfig/lights_fs_preferred_2007_wide_10.pdf", "$texfig/lights_fs_preferred_2008_wide_10.pdf", 
	//            "$texfig/lights_fs_preferred_2009_wide_10.pdf", "$texfig/lights_fs_preferred_2010_wide_10.pdf", 
	//            "$texfig/lights_fs_preferred_2011_wide_10.pdf", "$texfig/lights_fs_preferred_2012_wide_10.pdf", 
	//            "$texfig/figure_rd_lights_plots.tex"
	// Figure A7: "$texfig/rd_lights_coeffs_by_year_intens.pdf, "$texfig/figure_rd_lights_by_year_intens.tex"
	// Figure A9: "$texfig/diff_in_disc_lights_dt_150_hours.pdf", "$texfig/diff_in_disc_lights_dt_100_hours.pdf", 
	//            "$texfig/figure_diff_in_disc_lights_hours.tex"
	// Figure B2: "$texfig/rd_lights_coeffs_by_year_sens_kernel.pdf", "$texfig/rd_lights_coeffs_by_year_sens_bw.pdf",
	//            "$texfig/rd_lights_coeffs_by_year_sens_ses.pdf", "$texfig/rd_lights_coeffs_by_year_sens_fes.pdf",
	//            "$texfig/rd_lights_coeffs_by_year_sens_outliers.pdf", "$texfig/rd_lights_coeffs_by_year_sens_lightsvar.pdf",
	//            "$texfig/figure_rd_lights_by_year_sens.tex"
	// Figure B4: "$texfig/rd_lights_coeffs_by_year_falsif.pdf", "$texfig/figure_rd_lights_by_year_falsif.tex"
	// Figure B5: "$texfig/placebo_test_lights_rdrobust.pdf"
	// Figure B6: "$texfig/lights_fs_preferred_2002_wide_10.pdf", "$texfig/lights_fs_preferred_2003_wide_10.pdf", 
	//            "$texfig/lights_fs_preferred_2004_wide_10.pdf", "$texfig/lights_fs_preferred_2005_wide_10.pdf", 
	//            "$texfig/lights_fs_preferred_2006_wide_10.pdf", "$texfig/figure_rd_lights_plots_pre.tex" 
	// Table B5:  "$textab/table_rd_lights_pre.tex"
	
	
* O4. Generate all NSS regression tables, and one figure
do "$path_code/outputs/outputs_nss.do"
	// inputs: "$panel/panel_dataset_dd_nss_uncollapsed.dta", "$panel/panel_dataset_full.dta",
	//         "$results/nss_reg_results.dta", "$sens/nss_dd_randomization_test.dta"

	// Table 3:  "$textab/table_nss_first_stage.tex"
	// Table 5:  "$textab/table_nss_reduced_form.tex"
	// Table 7:  "$textab/table_nss_2sls.tex"
	// Table A6: "$textab/table_nss_first_stage_no_state_trends.tex"
	// Table A7: "$textab/table_nss_first_stage_2k_pop.tex"
	// Table A8: "$textab/table_nss_first_stage_q1.tex"
	// Table A9: "$textab/table_nss_first_stage_q25.tex"
	// Table A11: "$textab/table_nss_first_stage_selfgen_fuels.tex"
	// Table A14: "$textab/table_nss_fs_intens.tex"
	// Table A17: "$textab/table_nss_rf_intens.tex"
	// Table A20: "$textab/table_nss_fs_hours.tex"
	// Table A21: "$textab/table_nss_2sls_hours.tex"
	// Table A24: "$textab/table_nss_reduced_form_quintiles.tex"
	// Table A27: "$textab/table_nss_first_stage_by_exp_quartile.tex"
	// Table A29: "$textab/table_nss_2sls_under2k.tex"
	// Table B7: "$textab/table_nss_first_stage_pretrends.tex"
	// Table B8: "$textab/table_nss_reduced_form_pretrends.tex"
	// Figure B9: "$texfig/randomization_test_nss_extens_st_trends.pdf", "$texfig/randomization_test_nss_levels_st_trends.pdf",
	//            "$texfig/randomization_test_nss_logs_st_trends.pdf", "$texfig/figure_nss_randomization.tex"
	// Table B9:  "$textab/table_nss_fs_rf_rggvy_districts.tex"
	// Table B10: "$textab/table_nss_2sls_state_trends.tex"
	
	
* O5. Generate all non-NSS reduced-form tables and figures	
do "$path_code/outputs/outputs_rf_outcomes.do"
	// inputs: 	"$results/dd_outcomes_census_distlevel.dta", "$results/dd_outcomes_census_pooled.dta",
	//          "$results/dd_results_outcomes_ec_4years.dta", "$results/dd_results_outcomes_dise_allyears.dta", 
	//          "$results/nss_reg_results.dta",
	//          "$results/RDROBUST_outcomes_rf_census.dta", "$results/RDROBUST_outcomes_rf_census_dpr.dta",
	//          "$results/RDROBUST_outcomes_rf_census_hrs.dta", "$results/RDROBUST_outcomes_rf_census_badshapefiles.dta",
	//          "$results/RDROBUST_outcomes_rf_ec.dta", "$results/RDROBUST_outcomes_rf_ec_dpr.dta", 
	//          "$results/RDROBUST_outcomes_rf_ec_hrs.dta", "$results/RDROBUST_outcomes_rf_ec_badshapefiles.dta",
	//          "$results/RDROBUST_outcomes_rf_schools.dta", "$results/RDROBUST_outcomes_rf_schools_dpr.dta",
	//          "$results/RDROBUST_outcomes_rf_schools_hrs.dta", "$results/RDROBUST_outcomes_rf_schools_badshapefiles.dta",
	//          "$results/RDROBUST_outcomes_rf_secc.dta", "$results/RDROBUST_outcomes_rf_secc_dpr.dta",
	//          "$results/RDROBUST_outcomes_rf_secc_hrs.dta", "$results/RDROBUST_outcomes_rf_secc_badshapefiles.dta",
	//          "$results/RDROBUST_outcomes_rf_shrug.dta", "$results/RDROBUST_outcomes_rf_shrug_dpr.dta",
	//          "$results/RDROBUST_outcomes_rf_shrug_hrs.dta", "$results/RDROBUST_outcomes_rf_shrug_badshapefiles.dta",
	//          "$results/RDROBUST_smoothness_census.dta",
	//          "$results/RDROBUST plots rf outcomes preferred/secc11_rural_cons_pc_fs_inreg_10.pdf",
	//          "$results/RDROBUST plots rf outcomes preferred/ln_secc11_rural_cons_pc_fs_inreg_10.pdf",
	//          "$results/RDROBUST plots rf outcomes preferred/hh_ratio_fs_inreg_10.pdf",
	//          "$results/RDROBUST plots rf outcomes preferred/tot_p11_fs_inreg_10.pdf",
	//          "$results/RDROBUST plots rf outcomes preferred/pct_hh_mnth_inc_5_10_fs_inreg_10.pdf", 
	//          "$results/RDROBUST plots rf outcomes preferred/pct_hh_salaried_job_fs_inreg_10.pdf", 
	//          "$results/RDROBUST plots rf outcomes preferred/secc11_inc_cultiv_share_fs_inreg_10.pdf", 
	//          "$results/RDROBUST plots rf outcomes preferred/pct_06_11_fs_inreg_10.pdf", 
	//          "$results/RDROBUST plots rf outcomes preferred/hpca11_h_size_avg_fs_inreg_10.pdf", 
	//          "$results/RDROBUST plots rf outcomes preferred/work_pooled_ag_p_11_fs_inreg_10.pdf", 
	//          "$results/RDROBUST plots rf outcomes preferred/work_pooled_ag_m_11_fs_inreg_10.pdf", 
	//          "$results/RDROBUST plots rf outcomes preferred/work_pooled_ag_f_11_fs_inreg_10.pdf", 
	//          "$results/RDROBUST plots rf outcomes preferred/work_pooled_ot_p_11_fs_inreg_10.pdf", 
	//          "$results/RDROBUST plots rf outcomes preferred/work_pooled_ot_m_11_fs_inreg_10.pdf", 
	//          "$results/RDROBUST plots rf outcomes preferred/work_pooled_ot_f_11_fs_inreg_10.pdf", 
	//          "$results/RDROBUST plots rf outcomes preferred/ec_firms2013_fs_inreg_10.pdf", 
	//          "$results/RDROBUST plots rf outcomes preferred/ec_employees2013_fs_inreg_10.pdf", 
	//          "$results/RDROBUST plots rf outcomes preferred/g15_enroll_all2014_fs_inreg_10.pdf", 
	//          "$results/RDROBUST plots rf outcomes preferred/g68_enroll_all2014_fs_inreg_10.pdf", 
	//          "$results/RDROBUST plots rf outcomes preferred/tot_pass60_prev452014_fs_inreg_10.pdf", 
	//          "$results/RDROBUST plots rf outcomes preferred/tot_pass60_prev782014_fs_inreg_10.pdf", 
	//          "$results/RDROBUST plots rf outcomes preferred/pct_06_01_PRE_fs_inreg_10.pdf",
	//          "$results/RDROBUST plots rf outcomes preferred/work_p_01_PRE_fs_inreg_10.pdf", 
	//          "$results/RDROBUST plots rf outcomes preferred/work_f_01_PRE_fs_inreg_10.pdf", 
	//          "$results/RDROBUST plots rf outcomes preferred/index_vd_fin01_PRE_fs_inreg_10.pdf", 
	//          "$results/RDROBUST plots rf outcomes preferred/vd_pwr_d_any_01_PRE_fs_inreg_10.pdf", 
	//          "$results/RDROBUST plots rf outcomes preferred/vd_pwr_d_agr_01_PRE_fs_inreg_10.pdf", 
	//          "$results/RDROBUST plots rf outcomes preferred/vd_pwr_d_dom_01_PRE_fs_inreg_10.pdf", 
	//          "$results/RDROBUST plots rf outcomes preferred/vd_pwr_d_all_01_PRE_fs_inreg_10.pdf"
       
	// Table 4:    "$textab/table_rd_outcomes.tex"
	// Figure 7:   "$texfig/secc11_rural_cons_pc_fs_inreg_10.pdf", "$texfig/ln_secc11_rural_cons_pc_fs_inreg_10.pdf",
	//             "$texfig/hh_ratio_fs_inreg_10.pdf", "$texfig/tot_p11_fs_inreg_10.pdf", "$texfig/figure_rd_outcomes_main.tex"
	// Figure 8:   "$texfig/figure_rf_expenditure_hi_intens.eps", "$texfig/figure_rf_expenditure_hi_intens.tex" 
	// Figure 9:   "$texfig/figure_dd_ec_firms_by_popbin.eps", "$texfig/figure_dd_ec_employees_by_popbin.eps",
	//             "$texfig/figure_dd_ec_by_popbin.tex"
	// Table A12:  "$textab/table_dd_dist_msl_elec.tex"
	// Table A13:  "$textab/table_rd_msl_elec.tex"
	// Table A15:  "$textab/table_rd_outcomes_hi_intens.tex"
	// Table A19:  "$results/RDROBUST_outcomes_rf_schools_hrs.dta"
	// Table A22:  "$textab/table_rd_outcomes_bonus.tex"
	// Table A23:  "$textab/table_dd_outcomes.tex"
	// Figure A10: "$texfig/pct_hh_mnth_inc_5_10_fs_inreg_10.pdf", "$texfig/pct_hh_salaried_job_fs_inreg_10.pdf",
	//             "$texfig/secc11_inc_cultiv_share_fs_inreg_10.pdf", "$texfig/pct_06_11_fs_inreg_10.pdf",
	//             "$texfig/hpca11_h_size_avg_fs_inreg_10.pdf", "$texfig/figure_rd_secc.tex"
	// Figure A11: "$texfig/work_pooled_ag_p_11_fs_inreg_10.pdf", "$texfig/work_pooled_ag_m_11_fs_inreg_10.pdf",
	//             "$texfig/work_pooled_ag_f_11_fs_inreg_10.pdf", "$texfig/work_pooled_ot_p_11_fs_inreg_10.pdf",
	//             "$texfig/work_pooled_ot_m_11_fs_inreg_10.pdf", "$texfig/work_pooled_ot_f_11_fs_inreg_10.pdf",
	//             "$texfig/ec_firms2013_fs_inreg_10.pdf", "$texfig/ec_employees2013_fs_inreg_10.pdf", "$texfig/figure_rd_labor.tex"
	// Figure A12: "$texfig/g15_enroll_all2014_fs_inreg_10.pdf", "$texfig/g68_enroll_all2014_fs_inreg_10.pdf",
	//             "$texfig/tot_pass60_prev452014_fs_inreg_10.pdf", "$texfig/tot_pass60_prev782014_fs_inreg_10.pdf",
	//             "$texfig/figure_rd_schools.tex"
	// Table B1:   "$textab/table_rd_outcomes_sens_epa.tex"
	// Table B2:   "$textab/table_rd_outcomes_sens_uni.tex"
	// Table B3:   "$textab/table_rd_outcomes_sens_cer.tex"
	// Table B4:   "$textab/table_rd_outcomes_bad_shapefiles.tex"
	// Table B6:   "$textab/table_rd_cov_smoothness.tex"
	// Figure B7:  "$texfig/pct_06_01_PRE_fs_inreg_10.pdf", "$texfig/work_p_01_PRE_fs_inreg_10.pdf", 
	//             "$texfig/work_f_01_PRE_fs_inreg_10.pdf", "$texfig/index_vd_fin01_PRE_fs_inreg_10.pdf",
	//             "$texfig/vd_pwr_d_any_01_PRE_fs_inreg_10.pdf", "$texfig/vd_pwr_d_agr_01_PRE_fs_inreg_10.pdf",
	//             "$texfig/vd_pwr_d_dom_01_PRE_fs_inreg_10.pdf", "$texfig/vd_pwr_d_all_01_PRE_fs_inreg_10.pdf",
	//             "$texfig/figure_rd_cov_smoothness.tex"
		
		
* O6. Generate all fuzzy RD tables and figures	
do "$path_code/outputs/outputs_fuzzy_rd.do"
	// inputs: "$panel/panel_dataset_full.dta", "$results/RDROBUST_outcomes_fuzzy_census.dta", 
	//         "$results/RDROBUST_outcomes_fuzzy_ec.dta", "$results/RDROBUST_outcomes_fuzzy_schools.dta",
	//         "$results/RDROBUST_outcomes_fuzzy_secc.dta", "$results/RDROBUST_outcomes_fuzzy_secc_dpr.dta",
	//         "$results/RDROBUST_outcomes_fuzzy_shrug.dta", "$results/RDROBUST_outcomes_fuzzy_shrug_dpr.dta"
	
	// Table 6:    "$textab/table_rd_fuzzy_shrug.tex"
	// Table A16:  "$textab/table_rd_fuzzy_shrug_hi_intens.tex"
	// Figure A13: "$texfig/avg_hours_commercial_power_hist.pdf", "$texfig/2011_max_lights_hist.pdf",
	//             "$texfig/figure_endog_var_histograms.tex"
	// Figure A14: "$texfig/figure_scatter_lights_msl_elec.pdf", "$texfig/figure_scatter_lights_hours_com.pdf",
	//             "$texfig/figure_scatter_lights_correlations.tex"
	// Table A30:  "$textab/table_rd_outcomes_fuzzy_hours.tex"
	// Talbe A31:  "$textab/table_rd_outcomes_fuzzy_lights.tex"
	// Figure B8:  "$texfig/rd_fuzzy_coeffs_sens_cons.pdf", "$texfig/rd_fuzzy_coeffs_sens_ln_cons.pdf",
	//             "$texfig/figure_rd_fuzzy_shrug_sens.tex"
	

* O7. Generate all benefit-cost tables, and one figure	
do "$path_code/outputs/outputs_benefit_cost.do"
	// inputs: "$results/roi_results_expenditure_bootstraps.dta", "$results/roi_results_cs_irr.dta",
	//         "$results/expenditure_sampling_distributions.pdf", "$results/roi_results_cs_full.dta",
	//         "$panel/panel_dataset_dd_nss_uncollapsed.dta"

	// Table 8:    "$textab/table_roi_expenditure.tex"
	// Table 9:    "$textab/table_irr_cs.tex"
	// Figure A15: "$texfig/expenditure_sampling_distributions.pdf", "$texfig/figure_expenditure_sampling_dists.tex"
	// Table A25:  "$textab/table_roi_expenditure_sens.tex"
	// Table A26:  "$textab/table_irr_cs_fcost_lo.tex"
	// Table A28:  "$textab/table_irr_cs_components.tex"
		
		
*****************************************************************************************
*****************************************************************************************