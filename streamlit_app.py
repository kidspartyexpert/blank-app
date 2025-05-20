import streamlit as st
import pandas as pd

st.set_page_config(page_title="HDB Resale Estimator", layout="centered")
st.title("🏠 HDB Resale Price Estimator")

@st.cache_data
def load_hdb_data():
    df = pd.read_csv("hdb_data.gz", compression="gzip")
    df.columns = df.columns.str.lower()
    df['street_name'] = df['street_name'].str.upper().str.strip()
    df['block'] = df['block'].astype(str).str.upper().str.strip()
    df['flat_type'] = df['flat_type'].str.upper().str.strip()
    return df

df_hdb = load_hdb_data()

st.header("🔍 Search Property")
valid_streets = sorted(df_hdb['street_name'].unique())
address = st.selectbox("Street Name", valid_streets)

valid_blocks = sorted(df_hdb[df_hdb['street_name'] == address]['block'].unique())
block = st.selectbox("Block", valid_blocks)

valid_flat_types = sorted(
    df_hdb[(df_hdb['street_name'] == address) & (df_hdb['block'] == block)]['flat_type'].unique()
)
flat_type = st.selectbox("Flat Type", valid_flat_types)

block_floors = df_hdb[
    (df_hdb['street_name'] == address) &
    (df_hdb['block'] == block)
]['storey_range'].dropna().unique()

floor_numbers = set()
for r in block_floors:
    if "TO" in r:
        try:
            low = int(r.split(" TO ")[0])
            high = int(r.split(" TO ")[1])
            floor_numbers.update(range(low, high + 1))
        except:
            continue
valid_floors = sorted(floor_numbers)
floor_number = st.selectbox("Your Floor Number", valid_floors)

def categorize_floor_level(floor):
    if floor <= 6:
        return "Low Floor"
    elif floor <= 10:
        return "Mid Floor"
    else:
        return "High Floor"

def categorize_storey(storey):
    if isinstance(storey, str) and "TO" in storey:
        try:
            low = int(storey.split(" TO ")[0])
            if low <= 6:
                return "Low Floor"
            elif low <= 10:
                return "Mid Floor"
            else:
                return "High Floor"
        except:
            return "Unknown"
    return "Unknown"

def estimate_by_floor_group(df):
    df = df.copy()
    df['floor_group'] = df['storey_range'].apply(categorize_storey)
    if 'month' in df.columns:
        df['month'] = pd.to_datetime(df['month'], format='%Y-%m', errors='coerce')
    df = df[df['resale_price'].notnull()]
    df = df.sort_values(by='month', ascending=False)
    df['psf'] = df['resale_price'] / (df['floor_area_sqm'] * 10.7639)
    df['Price Range'] = df['resale_price'].apply(
        lambda x: f"SGD {int(max(0, x - 30000)):,} – {int(x):,}" if pd.notnull(x) else None
    )
    return df

def filter_results(df, address, block, flat_type):
    return df[
        (df['street_name'] == address) &
        (df['block'] == block) &
        (df['flat_type'] == flat_type)
    ]

if st.button("Estimate Price"):
    results = filter_results(df_hdb, address, block, flat_type)
    user_floor_group = categorize_floor_level(floor_number)

    if not results.empty:
        results = estimate_by_floor_group(results)
        floor_matches = results[results['floor_group'] == user_floor_group]

        if not floor_matches.empty:
            latest_price_range = floor_matches.iloc[0]['Price Range']
            st.markdown(f"""
                <div style="background-color:#f8f9fa;padding:0.8rem;margin-top:1rem;margin-bottom:1rem;
                    border-radius:10px;border:1px solid #ddd;text-align:center;">
                    <span style="font-size:1.2em;color:#2E8B57;font-weight:bold;">Estimated Price Range:</span><br>
                    <span style="font-size:1.5em;color:#2E8B57;">{latest_price_range}</span>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("#### 📊 3 Most Recent Transactions")
            recent_txns = floor_matches[['month', 'storey_range', 'resale_price']].head(3).copy()
            recent_txns['month'] = recent_txns['month'].dt.strftime('%d-%b-%Y')
            recent_txns['resale_price'] = recent_txns['resale_price'].apply(lambda x: f"${int(x):,}")
            recent_txns.columns = ['Date', 'Storey Range', 'Resale Price']
            st.dataframe(recent_txns, use_container_width=True, hide_index=True)

            avg_psf = floor_matches['psf'].mean()
            st.info(f"💡 Average PSF: SGD {avg_psf:,.2f}")

            avg_price_street = results['resale_price'].mean()
            st.info(f"📍 Average Price on {address}: SGD {avg_price_street:,.0f}")
        else:
            whatsapp_link = "https://wa.me/6593422768?text=Hi%20I%20saw%20your%20HDB%20resale%20tool%20and%20want%20to%20learn%20more"
            st.markdown(f"""
                <div style="background-color:#f8f9fa;padding:0.8rem;margin-top:1rem;margin-bottom:1rem;
                    border-radius:10px;border:1px solid #ddd;text-align:center;">
                    <span style="font-size:1.2em;color:#999;">No data, <a href="{whatsapp_link}" target="_blank">contact your agent to learn more</a></span>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("No matching records found. Try a different flat type or block.")

st.markdown("### 📱 Share This Tool")
st.caption("QR code functionality will be added soon.")

st.markdown("### 💬 What Sellers Are Saying")
st.success("“Sold my 4-room flat in Punggol 30k above valuation thanks to this estimator!”")
st.success("“Super helpful to know where my unit stands before talking to agents.”")

st.markdown("---")
st.markdown("### 🧑‍💼 Looking to Sell Your HDB Flat?")
st.markdown("""
Save **50% on agent fees** when you work directly with us.  
Get expert help and a full-service experience — without overpaying.

👇 *Tap the button below to chat instantly:*
""")

whatsapp_cta = "https://wa.me/6593422768?text=Hi%20I%20would%20like%20to%20sell%20my%20HDB%20flat"
st.markdown(f"""
<a href="{whatsapp_cta}" target="_blank">
    <button style="background-color:#25D366;color:white;padding:10px 18px;border:none;border-radius:6px;font-size:15px;cursor:pointer;">
        💬 Whatsapp Us Now
    </button>
</a>
""", unsafe_allow_html=True)
