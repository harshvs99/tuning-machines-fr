import streamlit as st
import pandas as pd

# --- Auth Check ---
if not st.session_state.get("authenticated", False):
    st.error("You must be logged in to view this page.")
    st.page_link("streamlit_app.py", label="Back to Login")
    st.stop()
# --- End Auth Check ---

st.title("Step 3: First Pass Analysis Report")

# --- Data Check ---
if not st.session_state.get("api_response") or not st.session_state.get("analysis_complete", False):
    st.warning("No analysis data found. Please run a new analysis first.")
    st.page_link("pages/2_Run_Analysis.py", label="Run New Analysis")
    st.stop()
# --- End Data Check ---

# --- Load Data ---
try:
    api_response = st.session_state.api_response
    l1_report = api_response['l1_analysis_report']
    scoring_report = api_response['scoring_report']
    discrepancy_report = api_response['discrepancy_report']
    company_name = l1_report.get('company_analysed', 'N/A')
    st.header(f"Analysis for: :orange[{company_name}]")
except (KeyError, TypeError) as e:
    st.error(f"Could not read analysis data from session state. Error: {e}")
    st.json(api_response)
    st.stop()

# --- NEW: Industry Discovery ---
try:
    # 1. Get industries from the report
    industry_report = l1_report.get('industry_analysis', {})
    claimed_industry = industry_report.get('claimed_industry')
    activity_industry = industry_report.get('activity_based_industry')
    
    # 2. Get existing preferences
    known_industries = st.session_state.industry_preferences.keys()
    
    # 3. Find new industries
    new_industries = []
    if claimed_industry and claimed_industry not in known_industries:
        new_industries.append(claimed_industry)
    if activity_industry and activity_industry not in known_industries:
        new_industries.append(activity_industry)
        
    # De-duplicate
    new_industries = list(set(new_industries))
    
    # 4. If new ones are found, update session state and show prompt
    if new_industries:
        st.session_state.new_industries_to_score = list(
            set(st.session_state.new_industries_to_score + new_industries)
        )
        st.info(
            f"**New Industries Found:** This analysis identified industries "
            f"({', '.join(new_industries)}) that are not in your preferences.",
            icon="💡"
        )
        st.page_link("pages/1_Portfolio_Setup.py", label="Go to Portfolio Setup to score them", icon="📊")

except Exception as e:
    st.warning(f"Could not check for new industries: {e}")
# --- END NEW ---


# --- Helper Function for Scorecard ---
def display_score(assessment_name: str):
    """Helper to display a rich score box."""
    try:
        score_data = scoring_report[assessment_name]
        score = score_data.get('score', 0)
        rating = score_data.get('rating', 'N/A')
        rationale = score_data.get('rationale', 'No rationale provided.')
        
        # Determine color based on score
        if score <= 1:
            color = "red"
        elif score == 2:
            color = "orange"
        elif score == 3:
            color = "blue"
        else: # 4 or 5
            color = "green"

        st.subheader(f"Overall Assessment: :{color}[{score}/5 ({rating})]")
        st.caption(f"**Rationale:** {rationale}")
        
        # Display identified risks if they exist
        risks = score_data.get('identified_risks')
        if risks:
            st.write("**Identified Risks for this Factor:**")
            risk_data = [{"Severity": r.get('severity'), "Factor": r.get('factor')} for r in risks]
            st.dataframe(risk_data, width='stretch')

    except (KeyError, TypeError):
        st.warning(f"No scoring data found for '{assessment_name}'.")

# --- Helper function to format large numbers (e.g., 440000000000 -> "₹440.0B") ---
def format_currency_inr(value):
    if value is None:
        return "N/A"
    # if value >= 1_00_00_00_00_00_000: # Trillion
    #     return f"₹{value / 1_00_00_00_00_00_000:.1f}T"
    if value >= 1_00_00_00_00_000: # Lakh Crores
        return f"₹{value / 1_00_00_00_00_000:.3f} Lakh Cr."
    # if value >= 1_00_00_00_000: # Crores (Billion)
    #     return f"₹{value / 1_00_00_00_000:.1f}B" # B for Billion (100 Cr)
    if value >= 1_00_00_000: # Crores
        return f"₹{value / 1_00_00_000:.2f} Cr."
    if value >= 1_00_000: # Lakhs
        return f"₹{value / 1_00_000:.1f} Lakh"
    return f"₹{value:,.0f}"

# --- UPDATED: Helper Function for Rich L1 Data ---
def display_l1_data(report_name: str):
    """Helper to display the raw L1 analysis in a formatted way."""
    try:
        report_data = l1_report[report_name]
        st.subheader("Detailed Analysis")
        
        # if report_name == 'founder_analysis':
        #     st.markdown(f"**Founder Count:** {report_data.get('founder_count')}")
            
        #     st.markdown("**Key Strengths:**")
        #     strengths_list = report_data.get('key_strengths', [])
        #     if strengths_list:
        #         st.markdown("\n".join([f"> - {s}" for s in strengths_list]))
        #     else:
        #         st.markdown("> - N/A")

        #     st.markdown("**Identified Gaps:**")
        #     gaps_list = report_data.get('identified_gaps', [])
        #     if gaps_list:
        #         st.markdown("\n".join([f"> - {g}" for g in gaps_list]))
        #     else:
        #         st.markdown("> - N/A")
            
        #     st.markdown(f"**Summary:** {report_data.get('summary', 'N/A')}")
        if report_name == 'founder_analysis':
            st.metric("Founder Count", report_data.get('founder_count', 'N/A'))
            
            founder_profiles = report_data.get('founder_profiles', [])
            
            if not founder_profiles:
                st.info("No detailed founder profiles were generated.")
            
            for profile in founder_profiles:
                with st.container(border=True):
                    st.subheader(f"👤 {profile.get('name', 'Unknown Founder')}")
                    
                    # Display the 4-quadrant ratings
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Tech Competency", f"{profile.get('tech_competency', 0)}/5")
                    col2.metric("Execution Ability", f"{profile.get('execution_ability', 0)}/5")
                    col3.metric("Management Exp.", f"{profile.get('management_experience', 0)}/5")
                    col4.metric("Sales Ability", f"{profile.get('sales_ability', 0)}/5")
                    
                    st.caption(f"**Profile Rationale:** {profile.get('profile_summary', 'N/A')}")
                    
                    with st.expander("View Detailed Skills"):
                        st.markdown("**Top 5 Skillsets:**")
                        skills = profile.get('top_5_skillsets', [])
                        if skills:
                            st.markdown("\n".join([f"- {s}" for s in skills]))
                        else:
                            st.markdown("- N/A")

                        st.markdown("**Special Skills:**")
                        special_skills = profile.get('special_skills', [])
                        if special_skills:
                            st.markdown("\n".join([f"- {s}" for s in special_skills]))
                        else:
                            st.markdown("- N/A")

            st.divider()
            
            # --- Display the team-level summary ---
            st.subheader("Team-Level Assessment")
            
            st.markdown("**Key Strengths (Team):**")
            strengths_list = report_data.get('key_strengths', [])
            st.markdown("\n".join([f"> - {s}" for s in strengths_list] or "> - N/A"))

            st.markdown("**Identified Gaps (Team):**")
            gaps_list = report_data.get('identified_gaps', [])
            st.markdown("\n".join([f"> - {g}" for g in gaps_list] or "> - N/A"))
            
            st.markdown(f"**Overall Summary:** {report_data.get('summary', 'N/A')}")

        elif report_name == 'product_analysis':
            st.markdown(f"**Core Product Offering:**")
            st.markdown(f"> {report_data.get('core_product_offering', 'N/A')}")
            
            st.markdown(f"**Problem Solved:**")
            st.markdown(f"> {report_data.get('problem_solved', 'N/A')}")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Qualitative Value Prop:**")
                st.info(report_data.get('value_proposition_qualitative', 'N/A'))
            with col2:
                st.markdown("**Quantitative Value Prop:**")
                st.success(report_data.get('value_proposition_quantitative', 'N/A'))

            st.markdown("**Direct Substitutes:**")
            subs = report_data.get('direct_substitutes', [])
            if subs:
                st.markdown("\n".join([f"- {s}" for s in subs]))
            else:
                st.markdown("- N/A")
            
            st.markdown(f"**Summary:** {report_data.get('summary', 'N/A')}")

        elif report_name == 'industry_analysis':
            col1, col2 = st.columns(2)
            col1.metric("Claimed Industry", report_data.get('claimed_industry', 'N/A'))
            col2.metric("Activity-Based Industry", report_data.get('activity_based_industry', 'N/A'))
            st.markdown(f"**Coherent with Claims:** {report_data.get('is_coherent_with_claims', 'N/A')}")
            
            # --- FIX for SyntaxError ---
            # Removed the extra `_(`
            st.markdown(f"**Summary:** {report_data.get('summary', 'N/A')}")
            
            with st.expander("View Porter's Five Forces Analysis"):
                porters = report_data.get('porter_five_forces_summary', {})
                if porters:
                    for force, analysis in porters.items():
                        st.markdown(f"**{force.replace('_', ' ').title()}:** {analysis}")
                else:
                    st.write("No Porter's analysis data found.")

        elif report_name == 'externalities_analysis':
            st.metric("Existential Threat Identified?", "Yes ❌" if report_data.get('existential_threat_identified') else "No ✅")
            st.markdown(f"**Summary:** {report_data.get('summary', 'N/A')}")
            
            risks = report_data.get('identified_risks', [])
            if risks:
                st.markdown("**PESTLE Risk Breakdown:**")
                df = pd.DataFrame(risks)
                st.dataframe(df[['category', 'impact', 'risk_description', 'rationale']], width='stretch')
            else:
                st.write("No specific PESTLE risks were identified.")

        elif report_name == 'competition_analysis':
            st.markdown("**Competitive Advantage:**")
            st.success(report_data.get('competitive_advantage', 'N/A'))
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Direct Competitors:**")
                comps = report_data.get('direct_competitors', [])
                if comps:
                    st.markdown("\n".join([f"- {c}" for c in comps]))
                else:
                    st.markdown("- N/A")
            with col2:
                st.markdown("**Best Alternative Solution:**")
                st.info(report_data.get('best_alternative_solution', 'N/A'))

            st.markdown("**Switching Costs Analysis:**")
            st.markdown(f"> {report_data.get('switching_costs_analysis', 'N/A')}")
            st.markdown(f"**Summary:** {report_data.get('summary', 'N/A')}")

        # --- THIS IS THE VISUALIZED FINANCIALS SECTION ---
        elif report_name == 'financial_analysis':
            
            # 1. Top-Line Assessment
            st.subheader("Financial Viability Assessment")
            viability = report_data.get('three_year_viability_check', {})
            viability_share = viability.get('required_som_share', 0) * 100
            if viability_share is not None:
                st.metric("Required SOM Share by Year 3", f"{viability_share:.2f}%")
            else:
                st.metric("Required SOM Share by Year 3", "N/A")

            # Show rationale, color-coded by score
            score_data = scoring_report.get("financial_assessment", {})
            if score_data.get('score', 0) <= 2:
                st.error(f"**Assessment:** {report_data.get('is_rational_assessment', 'N/A')}")
            else:
                st.success(f"**Assessment:** {report_data.get('is_rational_assessment', 'N/A')}")

            st.divider()

            # 2. Market Sizing (Deck vs. Analyst)
            st.subheader("Market Sizing (Deck vs. Analyst)")
            
            deck = report_data.get('deck_claims', {})
            analyst = report_data.get('analyst_sizing', {})
            
            market_data = [
                {"Market": "TAM", 
                 "Deck Claim": format_currency_inr(deck.get('tam')), 
                 "Analyst Sizing": format_currency_inr(analyst.get('tam'))},
                {"Market": "SAM", 
                 "Deck Claim": format_currency_inr(deck.get('sam')),  # Often null
                 "Analyst Sizing": format_currency_inr(analyst.get('sam'))},
                {"Market": "SOM", 
                 "Deck Claim": format_currency_inr(deck.get('som')), 
                 "Analyst Sizing": format_currency_inr(analyst.get('som'))}
            ]
            market_df = pd.DataFrame(market_data).set_index("Market")
            st.dataframe(market_df, width='stretch')

            st.info(f"**Discrepancy Rationale:** {report_data.get('sizing_discrepancy_rationale', 'N/A')}")
            
            st.divider()
            
            # 3. Unit Economics
            st.subheader("Unit Economics")
            ue = report_data.get('unit_economics', {})
            price = ue.get('price_per_unit', 0)
            vc = ue.get('variable_cost_per_unit', 0)
            margin = ue.get('contribution_margin_per_unit', 0)
            cac = ue.get('customer_acquisition_cost_cac', 0)

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Price per Unit", format_currency_inr(price))
            col2.metric("Variable Cost per Unit", format_currency_inr(vc))
            col3.metric("Contribution Margin", format_currency_inr(margin))
            col4.metric("Est. CAC", format_currency_inr(cac))
            
            st.divider()

            # 4. 3-Year Viability & Missing Data
            st.subheader("3-Year Viability Check")
            viability = report_data.get('three_year_viability_check', {})
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Annual Fixed Costs", format_currency_inr(viability.get('annual_fixed_costs')))
            col2.metric("One-Time Dev Costs", format_currency_inr(viability.get('one_time_development_costs')))
            col3.metric("Required Y3 Revenue", format_currency_inr(viability.get('required_annual_revenue_at_year_3')))

            missing = report_data.get('missing_data_callouts', [])
            if missing:
                with st.expander("Missing Data Callouts (Used for Estimates)"):
                    st.warning("- " + "\n- ".join(missing))
            
            st.markdown(f"**Summary:** {report_data.get('summary', 'N/A')}")
        
        # --- End of Financials Section ---

        elif report_name == 'synergy_analysis':
            st.markdown(f"**Summary:** {report_data.get('summary', 'N/A')}")
            col1, col2 = st.columns(2)
            col1.metric("Solves Identified Skill Gap?", "Yes ✅" if report_data.get('solves_identified_skill_gap') else "No ❌")
            col2.metric("Solves Identified External Threat?", "Yes ✅" if report_data.get('solves_identified_external_threat') else "No ❌")

            synergies = report_data.get('potential_synergies', [])
            if synergies:
                st.markdown("**Potential Synergies:**")
                df = pd.DataFrame(synergies)
                st.dataframe(df, width='stretch')
            else:
                st.markdown("*No specific portfolio synergies were identified.*")
        
        else:
            # Fallback for any unexpected report_name
            st.json(report_data, expanded=True)
            
    except (KeyError, TypeError) as e:
        st.warning(f"No L1 data found for '{report_name}'. Error: {e}")
        st.json(l1_report.get(report_name, {})) # Show raw data on error


# --- Main Tab Layout ---
tab_names = [
    "Executive Summary", 
    "🚩 Red Flags / Verification", 
    "1. Founder", "2. Industry", "3. Product", 
    "4. Externalities", "5. Competition", "6. Financials", "7. Synergies"
]
# Note the new 'tab_summary' and 'tab_red_flags' variables
tab_summary, tab_red_flags, tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(tab_names)

# --- NEW: Executive Summary Tab ---
with tab_summary:
    st.header("Executive Summary")
    
    try:
        # 1. Pull data from the L1 report
        product_data = l1_report.get('product_analysis', {})
        industry_data = l1_report.get('industry_analysis', {})
        competition_data = l1_report.get('competition_analysis', {})

        # 2. Display the "Value Chain" overview
        st.subheader("What is the business?")
        st.markdown(f"**Core Product Offering:**")
        st.markdown(f"> {product_data.get('core_product_offering', 'N/A')}")
        
        st.markdown(f"**Problem Solved:**")
        st.markdown(f"> {product_data.get('problem_solved', 'N/A')}")
        
        st.divider()

        st.subheader("Where do they fit in the market?")
        st.metric("Activity-Based Industry", industry_data.get('activity_based_industry', 'N/A'))
        st.markdown("**Competitive Advantage:**")
        st.success(f"{competition_data.get('competitive_advantage', 'N/A')}")

        # col1, col2 = st.columns(2)
        # col1.metric("Activity-Based Industry", industry_data.get('activity_based_industry', 'N/A'))
        
        # with col2:
        #     st.markdown("**Competitive Advantage:**")
        #     st.success(f"{competition_data.get('competitive_advantage', 'N/A')}")

        st.divider()

        # 3. Display the "At-a-Glance" Scorecard
        st.subheader("At-a-Glance Scorecard")
        score_data = []
        factor_keys = [
            ("founder_assessment", "Founder"),
            ("industry_assessment", "Industry"),
            ("product_assessment", "Product"),
            ("externalities_assessment", "Externalities"),
            ("competition_assessment", "Competition"),
            ("financial_assessment", "Financials"),
            ("synergy_assessment", "Synergies")
        ]
        
        for key, name in factor_keys:
            assessment = scoring_report.get(key, {})
            score_data.append({
                "Factor": name,
                "Score (1-5)": assessment.get('score', 'N/A'),
                "Rating": assessment.get('rating', 'N/A'),
                "Rationale": assessment.get('rationale', 'No rationale.')
            })
        
        score_df = pd.DataFrame(score_data).set_index("Factor")
        st.dataframe(
            score_df,
            column_config={
                "Rationale": st.column_config.TextColumn("Rationale", width="large")
            },
            width='stretch'
        )

    except Exception as e:
        st.error(f"Failed to build Executive Summary: {e}")
        st.json(api_response)

# --- Red Flags Tab (Renamed from tab_main to tab_red_flags) ---
with tab_red_flags: # <-- RENAMED VARIABLE
    st.header("Discrepancy & Verification Report")
    st.info("This report flags inconsistencies found between the pitch deck and external data. These form the basis for the Founder Q&A.")
    
    st.subheader("Assessed Findings (Red Flags)")
    # --- FIX for my previous bug (removed extra .get('discrepancy_report')) ---
    findings = discrepancy_report.get('assessed_findings', []) 
    if not findings:
        st.success("No significant discrepancies or 'Red Flags' were found.")
    else:
        for finding in findings:
            risk = finding.get('risk_assessment', 'N/A')
            if risk == "High Risk":
                st.error(f"**{risk}: {finding.get('claim')}**", icon="❌")
            elif risk == "Medium Risk":
                st.warning(f"**{risk}: {finding.get('claim')}**", icon="⚠️")
            else:
                st.info(f"**{risk}: {finding.get('claim')}**", icon="💡")
            
            st.markdown(f"**Finding:** {finding.get('finding_summary')}")
            st.markdown(f"**Impact:** {finding.get('material_impact_analysis')}")
            st.divider()

    st.subheader("Successfully Verified Claims")
    # --- FIX for my previous bug (removed extra .get('discrepancy_report')) ---
    verified = discrepancy_report.get('successfully_verified_claims', [])
    if not verified:
        st.info("No claims were marked for simple verification.")
    else:
        for claim in verified:
            st.success(f"**Verified:** {claim.get('claim')}", icon="✅")
            st.caption(f"**Source:** {claim.get('source_of_claim')} | **Finding:** {claim.get('finding')}")

# --- Agent 1: Founder ---
with tab1:
    display_score("founder_assessment")
    st.divider()
    display_l1_data("founder_analysis")

# --- Agent 2: Industry ---
with tab2:
    display_score("industry_assessment")
    st.divider()
    display_l1_data("industry_analysis")

# --- Agent 3: Product ---
with tab3:
    display_score("product_assessment")
    st.divider()
    display_l1_data("product_analysis")

# --- Agent 4: Externalities ---
with tab4:
    display_score("externalities_assessment")
    st.divider()
    display_l1_data("externalities_analysis")

# --- Agent 5: Competition ---
with tab5:
    display_score("competition_assessment")
    st.divider()
    display_l1_data("competition_analysis")

# --- Agent 6: Financials ---
with tab6:
    display_score("financial_assessment")
    st.divider()
    display_l1_data("financial_analysis")
    
# --- Agent 7: Synergies ---
with tab7:
    display_score("synergy_assessment")
    st.divider()
    display_l1_data("synergy_analysis")

st.divider()
st.page_link("pages/4_Founder_Q&A.py", label="Next Step: Go to Founder Q&A", icon="➡️")