import streamlit as st
import pandas as pd

# --- Auth Check ---
if not st.session_state.get("authenticated", False):
    st.error("You must be logged in to view this page.")
    st.page_link("streamlit_app.py", label="Back to Login")
    st.stop()
# --- End Auth Check ---

st.title("Step 5: Final Report (Post-Q&A)")

# --- Data Check ---
if not st.session_state.get("api_response"):
    st.warning("No analysis data found. Please run a new analysis first.")
    st.page_link("pages/2_Run_Analysis.py", label="Run New Analysis")
    st.stop()
# --- End Data Check ---

# --- Load Data ---
try:
    final_report = st.session_state.api_response
    l1_report_data = final_report['l1_analysis_report']
    final_scoring_report = final_report['scoring_report']
    qa_transcript = final_report.get('founder_qa_transcript', [])
    
    # Check for the backup
    original_report_backup = st.session_state.get('l1_api_response_backup')
    has_backup = bool(original_report_backup)
    
    if has_backup:
        original_scoring_report = original_report_backup.get('scoring_report', {})
    else:
        original_scoring_report = {}

    company_name = l1_report_data.get('company_analysed', 'N/A')
    st.header(f"Final Analysis for: :orange[{company_name}]")

except (KeyError, TypeError) as e:
    st.error(f"Could not read the analysis data. It might be in an old format. Error: {e}")
    st.json(st.session_state.api_response)
    st.stop()

# --- Q&A Transcript Expander ---
with st.expander("View Founder Q&A Transcript"):
    if qa_transcript:
        for message in qa_transcript:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    elif has_backup:
        st.info("A Q&A session was run, but the transcript was not saved in this report format.")
    else:
        st.info("No Q&A session was run for this analysis.")

# --- Helper Functions (Copied from 3_First_Pass_Report.py and modified) ---

def format_currency_inr(value):
    """Formats large numbers into Indian currency (Lakh, Crore)."""
    if value is None:
        return "N/A"
    # if value >= 1_00_00_00_00_00_000: # Trillion
    #     return f"₹{value / 1_00_00_00_00_00_000:.1f}T"
    if value >= 1_00_00_00_00_000: # Lakh Crores
        return f"₹{value / 1_00_00_00_00_000:.1f}Lakh Cr"
    # if value >= 1_00_00_00_000: # Crores (Billion)
    #     return f"₹{value / 1_00_00_00_000:.1f}B" # B for Billion (100 Cr)
    if value >= 1_00_00_000: # Crores
        return f"₹{value / 1_00_00_000:.1f} Cr"
    if value >= 1_00_000: # Lakhs
        return f"₹{value / 1_00_000:.1f} Lakh"
    return f"₹{value:,.0f}"

def display_score(assessment_name: str, new_score_data: dict, old_score_data: dict, has_backup: bool):
    """
    Displays the final score, and compares it to the old score if available.
    """
    try:
        new_score = new_score_data.get('score', 0)
        rating = new_score_data.get('rating', 'N/A')
        rationale = new_score_data.get('rationale', 'No rationale provided.')
        
        # Determine color based on score
        if new_score <= 1:
            color = "red"
        elif new_score == 2:
            color = "orange"
        elif new_score == 3:
            color = "blue"
        else: # 4 or 5
            color = "green"

        st.subheader(f"Final Assessment: :{color}[{new_score}/5 ({rating})]")
        
        # --- NEW: Show score comparison ---
        if has_backup:
            old_score = old_score_data.get('score', 0)
            delta = new_score - old_score
            if delta > 0:
                delta_str = f"▲ +{delta}"
                delta_color = "normal"
            elif delta < 0:
                delta_str = f"▼ {delta}"
                delta_color = "inverse"
            else:
                delta_str = "No Change"
                delta_color = "off"
            
            st.metric(
                label="Score Evolution (Post-Q&A)",
                value=f"{new_score}/5",
                delta=delta_str,
                delta_color=delta_color,
                help=f"The score changed from {old_score}/5 to {new_score}/5 after the Founder Q&A."
            )
        # --- END NEW ---
        
        st.caption(f"**Final Rationale:** {rationale}")
        
        risks = new_score_data.get('identified_risks')
        if risks:
            st.write("**Identified Risks for this Factor:**")
            risk_data = [{"Severity": r.get('severity'), "Factor": r.get('factor')} for r in risks]
            st.dataframe(risk_data, width='stretch')

    except (KeyError, TypeError):
        st.warning(f"No scoring data found for '{assessment_name}'.")


def display_l1_data(report_name: str, l1_report: dict, scoring_report: dict):
    """
    Helper to display the raw L1 analysis in a formatted way.
    (This is the same as 3_First_Pass_Report.py, just made into a function)
    """
    try:
        report_data = l1_report[report_name]
        st.subheader("Detailed Analysis (Updated)")
        
        # if report_name == 'founder_analysis':
            # st.markdown(f"**Founder Count:** {report_data.get('founder_count')}")
            # st.markdown("**Key Strengths:**")
            # st.markdown("\n".join([f"> - {s}" for s in report_data.get('key_strengths', [])] or "> - N/A"))
            # st.markdown("**Identified Gaps:**")
            # st.markdown("\n".join([f"> - {g}" for g in report_data.get('identified_gaps', [])] or "> - N/A"))
            # st.markdown(f"**Summary:** {report_data.get('summary', 'N/A')}")
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
            st.markdown(f"**Core Product Offering:**\n> {report_data.get('core_product_offering', 'N/A')}")
            st.markdown(f"**Problem Solved:**\n> {report_data.get('problem_solved', 'N/A')}")
            col1, col2 = st.columns(2)
            col1.info(f"**Qualitative Value:** {report_data.get('value_proposition_qualitative', 'N/A')}")
            col2.success(f"**Quantitative Value:** {report_data.get('value_proposition_quantitative', 'N/A')}")
            st.markdown("**Direct Substitutes:**")
            st.markdown("\n".join([f"- {s}" for s in report_data.get('direct_substitutes', [])] or "- N/A"))
            st.markdown(f"**Summary:** {report_data.get('summary', 'N/A')}")

        elif report_name == 'industry_analysis':
            col1, col2 = st.columns(2)
            col1.metric("Claimed Industry", report_data.get('claimed_industry', 'N/A'))
            col2.metric("Activity-Based Industry", report_data.get('activity_based_industry', 'N/A'))
            st.markdown(f"**Coherent with Claims:** {report_data.get('is_coherent_with_claims', 'N/A')}")
            st.markdown(f"**Summary:** {report_data.get('summary', 'N/A')}")
            with st.expander("View Porter's Five Forces Analysis"):
                porters = report_data.get('porter_five_forces_summary', {})
                st.json(porters, expanded=True)

        elif report_name == 'externalities_analysis':
            st.metric("Existential Threat Identified?", "Yes ❌" if report_data.get('existential_threat_identified') else "No ✅")
            st.markdown(f"**Summary:** {report_data.get('summary', 'N/A')}")
            risks = report_data.get('identified_risks', [])
            if risks:
                st.markdown("**PESTLE Risk Breakdown:**")
                st.dataframe(pd.DataFrame(risks), width='stretch')

        elif report_name == 'competition_analysis':
            st.success(f"**Competitive Advantage:** {report_data.get('competitive_advantage', 'N/A')}")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Direct Competitors:**")
                st.markdown("\n".join([f"- {c}" for c in report_data.get('direct_competitors', [])] or "- N/A"))
            with col2:
                st.markdown("**Best Alternative Solution:**")
                st.info(report_data.get('best_alternative_solution', 'N/A'))
            st.markdown(f"**Switching Costs:** {report_data.get('switching_costs_analysis', 'N/A')}")
            st.markdown(f"**Summary:** {report_data.get('summary', 'N/A')}")

        elif report_name == 'financial_analysis':
            st.subheader("Financial Viability Assessment")
            viability = report_data.get('three_year_viability_check', {})
            viability_share = viability.get('required_som_share', 0) * 100
            st.metric("Required SOM Share by Year 3", f"{viability_share:.2f}%")
            
            score_data = scoring_report.get("financial_assessment", {})
            assessment_text = report_data.get('is_rational_assessment', 'N/A')
            if score_data.get('score', 0) <= 2:
                st.error(f"**Assessment:** {assessment_text}")
            else:
                st.success(f"**Assessment:** {assessment_text}")
            
            st.divider()
            st.subheader("Market Sizing (Deck vs. Analyst)")
            deck = report_data.get('deck_claims', {})
            analyst = report_data.get('analyst_sizing', {})
            market_data = [
                {"Market": "TAM", "Deck Claim": format_currency_inr(deck.get('tam')), "Analyst Sizing": format_currency_inr(analyst.get('tam'))},
                {"Market": "SAM", "Deck Claim": format_currency_inr(deck.get('sam')), "Analyst Sizing": format_currency_inr(analyst.get('sam'))},
                {"Market": "SOM", "Deck Claim": format_currency_inr(deck.get('som')), "Analyst Sizing": format_currency_inr(analyst.get('som'))}
            ]
            st.dataframe(pd.DataFrame(market_data).set_index("Market"), width='stretch')
            st.info(f"**Discrepancy Rationale:** {report_data.get('sizing_discrepancy_rationale', 'N/A')}")
            
            st.divider()

            st.subheader("Unit Economics")
            ue = report_data.get('unit_economics', {})
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Price/Unit", format_currency_inr(ue.get('price_per_unit')))
            col2.metric("Cost/Unit", format_currency_inr(ue.get('variable_cost_per_unit')))
            col3.metric("Margin", format_currency_inr(ue.get('contribution_margin_per_unit')))
            col4.metric("Est. CAC", format_currency_inr(ue.get('customer_acquisition_cost_cac')))
            
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

        elif report_name == 'synergy_analysis':
            st.markdown(f"**Summary:** {report_data.get('summary', 'N/A')}")
            col1, col2 = st.columns(2)
            col1.metric("Solves Identified Skill Gap?", "Yes ✅" if report_data.get('solves_identified_skill_gap') else "No ❌")
            col2.metric("Solves Identified External Threat?", "Yes ✅" if report_data.get('solves_identified_external_threat') else "No ❌")
            synergies = report_data.get('potential_synergies', [])
            if synergies:
                st.markdown("**Potential Synergies:**")
                st.dataframe(pd.DataFrame(synergies), width='stretch')
        
        else:
            st.json(report_data, expanded=True)
            
    except (KeyError, TypeError) as e:
        st.warning(f"No L1 data found for '{report_name}'. Error: {e}")
        st.json(l1_report.get(report_name, {}))


# --- Main Tab Layout ---
tab_names = [
    "📊 Score Evolution", 
    "1. Founder", "2. Industry", "3. Product", 
    "4. Externalities", "5. Competition", "6. Financials", "7. Synergies"
]
tab_summary, tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(tab_names)

with tab_summary:
    st.header("Score Evolution (Pre-Q&A vs. Post-Q&A)")
    if not has_backup:
        st.info("No pre-Q&A analysis was saved, so no score comparison is available.")
        st.write("The scores shown in other tabs are the final scores.")
    else:
        st.info("This table summarizes the change in scores after the Founder Q&A.")
        factors = ["founder", "industry", "product", "externalities", "competition", "financial", "synergy"]
        data = []
        for f in factors:
            key = f"{f}_assessment"
            old_data = original_scoring_report.get(key, {})
            new_data = final_scoring_report.get(key, {})
            
            old_score = old_data.get('score', 'N/A')
            new_score = new_data.get('score', 'N/A')
            
            change = "N/A"
            if isinstance(old_score, int) and isinstance(new_score, int):
                delta = new_score - old_score
                if delta > 0:
                    change = f"▲ +{delta}"
                elif delta < 0:
                    change = f"▼ {delta}"
                else:
                    change = "No Change"
            
            data.append({
                "Factor": f.title(),
                "Old Score": old_score,
                "New Score": new_score,
                "Change": change,
                "Final Rating": new_data.get('rating', 'N/A')
            })
        
        df = pd.DataFrame(data).set_index("Factor")
        st.dataframe(df, width='stretch')

    # --- NEWLY ADDED SECTION ---
    st.divider()
    st.subheader("📌 Company Investment Recommendation")
    st.write("Assign a weight to each factor to generate a custom-weighted recommendation score.")

    # Create sliders to understand the importance of each section for the analyst
    col1, col2 = st.columns(2)
    founder_weight = col1.select_slider("Founder Analysis Weightage", options=["Not Important", "Somewhat Important", "Important", "Very Important", "Most Important"], value="Important")
    industry_weight = col2.select_slider("Industry Analysis Weightage", options=["Not Important", "Somewhat Important", "Important", "Very Important", "Most Important"], value="Important")
    product_weight = col1.select_slider("Product Analysis Weightage", options=["Not Important", "Somewhat Important", "Important", "Very Important", "Most Important"], value="Very Important")
    financial_weight = col2.select_slider("Financial Analysis Weightage", options=["Not Important", "Somewhat Important", "Important", "Very Important", "Most Important"], value="Very Important")
    externalities_weight = col1.select_slider("Externalities & Risks Weightage", options=["Not Important", "Somewhat Important", "Important", "Very Important", "Most Important"], value="Somewhat Important")
    competition_weight = col2.select_slider("Competition Analysis Weightage", options=["Not Important", "Somewhat Important", "Important", "Very Important", "Most Important"], value="Somewhat Important")

    # Convert each weight to a numeric scale (0-5)
    weight_map = {
        "Not Important": 0,
        "Somewhat Important": 1,
        "Important": 3,
        "Very Important": 4,
        "Most Important": 5
    }

    weights = {
        "founder": weight_map[founder_weight],
        "industry": weight_map[industry_weight],
        "product": weight_map[product_weight],
        "financial": weight_map[financial_weight],
        "externalities": weight_map[externalities_weight],
        "competition": weight_map[competition_weight]
    }

    # Get the final scores from the report
    # Note: This uses the 'final_scoring_report' variable loaded at the top
    founder_assessment = final_scoring_report.get("founder_assessment", {}).get("score", 0)
    industry_assessment = final_scoring_report.get("industry_assessment", {}).get("score", 0)
    product_assessment = final_scoring_report.get("product_assessment", {}).get("score", 0)
    financial_assessment = final_scoring_report.get("financial_assessment", {}).get("score", 0)
    externalities_assessment = final_scoring_report.get("externalities_assessment", {}).get("score", 0)
    competition_assessment = final_scoring_report.get("competition_assessment", {}).get("score", 0)
    
    # Total weighted is a weighted average of the assessments
    total_weighted_score = (
        (founder_assessment * weights["founder"]) +
        (industry_assessment * weights["industry"]) +
        (product_assessment * weights["product"]) +
        (financial_assessment * weights["financial"]) +
        (externalities_assessment * weights["externalities"]) +
        (competition_assessment * weights["competition"])
    ) / (sum(weights.values()) if sum(weights.values()) > 0 else 1)
    
    # Scale to 100 for the metric
    final_score_100 = round(total_weighted_score * 20, 2) # (Score / 5) * 100 = Score * 20

    # Display the recommendation
    st.metric("Overall Investment Recommendation Score", f"{final_score_100} / 100.0")
    
    # --- END OF NEWLY ADDED SECTION ---


# --- Individual Agent Tabs ---
# Each tab now passes the correct data to the modified helpers

def render_tab(tab, name_key, analysis_key):
    with tab:
        assessment_key = f"{name_key}_assessment"
        display_score(
            assessment_key,
            final_scoring_report.get(assessment_key, {}),
            original_scoring_report.get(assessment_key, {}),
            has_backup
        )
        st.divider()
        display_l1_data(
            f"{name_key}_analysis",
            l1_report_data,
            final_scoring_report
        )

render_tab(tab1, "founder", "founder_analysis")
render_tab(tab2, "industry", "industry_analysis")
render_tab(tab3, "product", "product_analysis")
render_tab(tab4, "externalities", "externalities_analysis")
render_tab(tab5, "competition", "competition_analysis")
render_tab(tab6, "financial", "financial_analysis")
render_tab(tab7, "synergy", "synergy_analysis")


st.divider()
st.page_link("pages/6_Generate_Deal_Note.py", label="Next Step: Generate Deal Note", icon="➡️")