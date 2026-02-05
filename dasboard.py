import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from datetime import datetime
import numpy as np

# Set style untuk visualisasi
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)

# ===========================
# KONFIGURASI HALAMAN
# ===========================
st.set_page_config(
    page_title="Dashboard E-Commerce Analysis",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)
# LOAD DATA
# ===========================
@st.cache_data
def load_data():
    # Load main dataset
    df = pd.read_csv(r'C:\Users\ASUS\OneDrive\New folder\OneDrive\Pictures\Documents\2. Kursus Dicoding\ANS_Projek Fundamental Analisis Data\Dasboard\all_data_ans.csv')  # ← GANTI PATH INI
    
    # Load translation
    df_translation = pd.read_csv(r'C:\Users\ASUS\OneDrive\New folder\OneDrive\Pictures\Documents\2. Kursus Dicoding\ANS_Projek Fundamental Analisis Data\Data\product_category_name_translation.csv')  # ← GANTI PATH INI
    
    # Merge untuk translate kategori
    df = df.merge(
        df_translation,
        on='product_category_name',
        how='left'
    )
    # Convert kolom datetime
    datetime_columns = [
        'order_purchase_timestamp',
        'order_approved_at', 
        'order_delivered_carrier_date',
        'order_delivered_customer_date',
        'order_estimated_delivery_date',
        'shipping_limit_date'
    ]
    
    for col in datetime_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    return df

# Load data
df = load_data()

# ===========================
# SIDEBAR - FILTER
# ===========================
st.sidebar.title("🔍 Filter Data")
st.sidebar.markdown("---")

# Filter berdasarkan tahun
st.sidebar.subheader("Periode Analisis")
years = sorted(df['order_purchase_timestamp'].dt.year.dropna().unique())
selected_years = st.sidebar.multiselect(
    "Pilih Tahun:",
    options=years,
    default=years
)

# Filter data berdasarkan tahun
df_filtered = df[df['order_purchase_timestamp'].dt.year.isin(selected_years)]

# Filter berdasarkan tanggal pembelian
min_date = df_filtered['order_purchase_timestamp'].min().date()
max_date = df_filtered['order_purchase_timestamp'].max().date()

date_range = st.sidebar.date_input(
    "Rentang Tanggal Detail:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:
    start_date, end_date = date_range
    df_filtered = df_filtered[
        (df_filtered['order_purchase_timestamp'].dt.date >= start_date) & 
        (df_filtered['order_purchase_timestamp'].dt.date <= end_date)
    ]

# Filter berdasarkan status order
st.sidebar.markdown("---")
order_statuses = st.sidebar.multiselect(
    "Status Order:",
    options=sorted(df['order_status'].dropna().unique()),
    default=['delivered']  # Default hanya yang delivered untuk analisis revenue
)
df_filtered = df_filtered[df_filtered['order_status'].isin(order_statuses)]

st.sidebar.markdown("---")
st.sidebar.info(f"📊 Total Orders: {df_filtered['order_id'].nunique():,}")
st.sidebar.info(f"📅 Periode: {df_filtered['order_purchase_timestamp'].min().strftime('%Y-%m-%d')} s/d {df_filtered['order_purchase_timestamp'].max().strftime('%Y-%m-%d')}")

# ===========================
# HEADER
# ===========================
st.title("🛒 Dashboard Analisis E-Commerce")
st.markdown("**Analisis Data Penjualan Brazilian E-Commerce Public Dataset Periode 2016–2018**")
st.markdown("*Ahmad Nurus Sholihin : ansstatistika295@gmail.com*")
st.markdown("---")

# ===========================
# KPI
# ===========================
st.subheader("📈 Performance Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_orders = df_filtered['order_id'].nunique()
    st.metric(
        label="Total Pesanan",
        value=f"{total_orders:,}"
    )

with col2:
    total_revenue = df_filtered['total_payment_value'].sum()
    st.metric(
        label="Total Pendapatan",
        value=f"R$ {total_revenue:,.2f}"
    )

with col3:
    avg_order_value = df_filtered['total_payment_value'].mean()
    st.metric(
        label="Rata-rata Nilai Pesanan",
        value=f"R$ {avg_order_value:,.2f}"
    )

with col4:
    unique_customers = df_filtered['customer_unique_id'].nunique()
    st.metric(
        label="Jumlah Pembeli Unik",
        value=f"{unique_customers:,}"
    )

st.markdown("---")

# ===========================
# PERTANYAAN BISNIS 1 - REVISI TOTAL
# ===========================
st.subheader("❓ Pertanyaan Bisnis 1: Kategori Produk dengan Kontribusi Pendapatan Terbesar")
st.markdown("**Kategori produk apa yang memberikan kontribusi pendapatan terbesar pada E-Commerce selama periode 2016–2018?**")

df_filtered_q1 = df_filtered.dropna(subset=['product_id', 'price', 'product_category_name_english'])

# LOGIKA Perhitungan yang Dipakai:
# - Total_Revenue = sum(price) 
# - Total_Orders = nunique(order_id) 
# - Avg_Order_Value = mean(price)
# - Revenue_Contribution = (Total_Revenue / total_all_revenue) * 100

revenue_by_category = df_filtered_q1.groupby('product_category_name_english').agg({
    'price': ['sum', 'mean'],  # sum = Total Revenue, mean = Avg Order Value
    'order_id': 'nunique',     # nunique = Total Orders (unique)
    'product_id': 'count',     # count = Total Items
    'review_score_avg': 'mean' # Review score
}).reset_index()

revenue_by_category.columns = ['category', 'total_revenue', 'avg_order_value', 'total_orders', 'total_items', 'avg_review']
revenue_by_category = revenue_by_category.sort_values('total_revenue', ascending=False)

# Hitung persentase kontribusi
total_all_revenue = revenue_by_category['total_revenue'].sum()
revenue_by_category['revenue_contribution_pct'] = (revenue_by_category['total_revenue'] / total_all_revenue) * 100

tab1, tab2 = st.tabs(["📊 Visualisasi", "📋 Data"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Top 10 Kategori Berdasarkan Total Pendapatan")
        
        top_10_categories = revenue_by_category.head(10).copy()
        
        fig, ax = plt.subplots(figsize=(10, 8))
        bars = ax.barh(range(len(top_10_categories)), top_10_categories['total_revenue'], 
                        color='#2ecc71', alpha=0.8)
        ax.set_yticks(range(len(top_10_categories)))
        ax.set_yticklabels(top_10_categories['category'])
        ax.set_xlabel('Total Pendapatan (R$)', fontsize=20, fontweight='bold')
        ax.set_ylabel('Product Category', fontsize=20, fontweight='bold')
        ax.set_title('Top 10 Product Categories by Total Revenue', fontsize=14, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.5, axis='x')
        
        # Tambahkan nilai dan persentase
        for i, (bar, row) in enumerate(zip(bars, top_10_categories.itertuples())):
            value = row.total_revenue
            pct = row.revenue_contribution_pct
            ax.text(value, i, f' R$ {value/1000:.0f}K ({pct:.1f}%)', 
                    va='center', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
        
    with col2:
        st.markdown("##### Kontribusi Pendapatan per Kategori (%)")
        
        # Pie chart untuk top 5
        top_5_revenue = revenue_by_category.head(5).copy()
        others_revenue = revenue_by_category.iloc[5:]['total_revenue'].sum()
        
        pie_data = pd.concat([
            top_5_revenue[['category', 'total_revenue']].set_index('category')['total_revenue'],
            pd.Series({'Others': others_revenue})
        ])
        
        fig, ax = plt.subplots(figsize=(10, 8))
        colors = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6', '#95a5a6']
        wedges, texts, autotexts = ax.pie(
            pie_data.values, 
            labels=pie_data.index,
            autopct='%1.1f%%',
            colors=colors,
            startangle=90,
            textprops={'fontsize': 14}
        )
        ax.set_title('Distribusi Pendapatan: Top 5 Categories vs Others', 
                    fontsize=14, fontweight='bold', pad=20)
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(24)
        
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
    
    # Visualisasi tambahan: Perbandingan Revenue vs Orders
    st.markdown("##### Analisis Pendapatan vs Jumlah Pesanan (Top 15)")
    
    top_15 = revenue_by_category.head(15).copy()
    
    fig, ax1 = plt.subplots(figsize=(14, 6))
    
    x = range(len(top_15))
    
    # Bar chart untuk revenue
    ax1.bar(x, top_15['total_revenue'], color='#3498db', alpha=0.7, label='Total Pendapatan (R$)')
    ax1.set_xlabel('Kategori Produk', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Total Pendapatan (R$)', fontsize=12, fontweight='bold', color='#3498db')
    ax1.tick_params(axis='y', labelcolor='#3498db')
    ax1.set_xticks(x)
    ax1.set_xticklabels(top_15['category'], rotation=45, ha='right')
    
    # Line plot untuk unique orders
    ax2 = ax1.twinx()
    ax2.plot(x, top_15['total_orders'], color='#e74c3c', marker='o', linewidth=2.5, 
            markersize=8, label='Unique Orders')
    ax2.set_ylabel('Number of Unique Orders', fontsize=12, fontweight='bold', color='#e74c3c')
    ax2.tick_params(axis='y', labelcolor='#e74c3c')
    
    ax1.set_title('Pendapatan vs Jumlah Pesanan per Kategori', fontsize=14, fontweight='bold', pad=20)
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')
    ax1.grid(True, alpha=0.5, axis='y')
    
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

with tab2:
    st.markdown("##### Statistik Detail per Kategori")
    
    # Buat tabel statistik lengkap
    category_stats_table = revenue_by_category.copy()
    category_stats_table = category_stats_table[[
        'category', 'total_revenue', 'total_orders', 'total_items',
        'avg_order_value', 'revenue_contribution_pct', 'avg_review'
    ]]
    
    # Rename columns untuk clarity
    category_stats_table.columns = [
        'Category', 'Total Revenue (R$)', 'Total Orders (Unique)', 'Total Items',
        'Avg Order Value (R$)', 'Revenue Contribution (%)', 'Avg Review Score'
    ]
    
    # Format numbers
    category_stats_table['Total Revenue (R$)'] = category_stats_table['Total Revenue (R$)'].apply(lambda x: f"R$ {x:,.2f}")
    category_stats_table['Avg Order Value (R$)'] = category_stats_table['Avg Order Value (R$)'].apply(lambda x: f"R$ {x:.2f}")
    category_stats_table['Revenue Contribution (%)'] = category_stats_table['Revenue Contribution (%)'].apply(lambda x: f"{x:.2f}%")
    category_stats_table['Avg Review Score'] = category_stats_table['Avg Review Score'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
    
    st.dataframe(category_stats_table.head(20), use_container_width=True)
    
    st.markdown("---")
    st.markdown("##### 📊 Validasi Metodologi")
    
    col_val1, col_val2, col_val3, col_val4 = st.columns(4)
    
    with col_val1:
        st.metric(
            "✅ Total Kategori",
            len(revenue_by_category)
        )
    
    with col_val2:
        top_3_contribution = revenue_by_category.head(3)['revenue_contribution_pct'].sum()
        st.metric(
            "📈 Kontribusi Top 3",
            f"{top_3_contribution:.1f}%"
        )
    
    with col_val3:
        top_category = revenue_by_category.iloc[0]['category']
        st.metric(
            "🏆 Kategori Teratas",
            top_category[:20]
        )
    
    with col_val4:
        top_cat_revenue = revenue_by_category.iloc[0]['total_revenue']
        st.metric(
            "💰 Revenue Teratas",
            f"R$ {top_cat_revenue/1000:.0f}K"
        )
    
    st.markdown("---")
with st.expander("💡 Insight & Kesimpulan"):
    # Hitung insights otomatis dengan LOGIKA BENAR
    top_cat = revenue_by_category.iloc[0]
    top_cat_name = top_cat['category']
    top_cat_revenue = top_cat['total_revenue']
    top_cat_pct = top_cat['revenue_contribution_pct']
    top_cat_orders = top_cat['total_orders']
    top_cat_aov = top_cat['avg_order_value']
    
    top_3_total = revenue_by_category.head(3)['total_revenue'].sum()
    top_3_pct = (top_3_total / total_all_revenue) * 100
    
    top_5_names = revenue_by_category.head(5)['category'].tolist()
    top_5_total = revenue_by_category.head(5)['total_revenue'].sum()
    top_5_pct = (top_5_total / total_all_revenue) * 100
    
    st.write(f"""
    **Temuan Utama :**
    
    1. **Kategori Teratas:** 
       - Kategori **{top_cat_name}** memberikan kontribusi revenue terbesar dengan total **R$ {top_cat_revenue:,.2f}** ({top_cat_pct:.1f}% dari total revenue)
       - Terdapat **{top_cat_orders:,} unique orders** dengan average order value **R$ {top_cat_aov:.2f}**
    
    2. **Dominasi Top Kategori:**
       - Top 3 kategori berkontribusi **{top_3_pct:.1f}%** dari total revenue
       - Top 5 kategori berkontribusi **{top_5_pct:.1f}%** dari total revenue
       - Menunjukkan **konsentrasi revenue** yang tinggi pada beberapa kategori utama
    
    3. **Distribusi Revenue:**
       - Total terdapat **{len(revenue_by_category)}** kategori aktif
       - Kategori dengan AOV tinggi: {revenue_by_category.nlargest(3, 'avg_order_value')['category'].tolist()}
       - Kategori dengan orders terbanyak: {revenue_by_category.nlargest(3, 'total_orders')['category'].tolist()}
    
    **Kesimpulan Bisnis:**
    
    Fokus strategi marketing dan inventory management sebaiknya **diprioritaskan** pada top 5 kategori:
    **{', '.join([cat[:25] for cat in top_5_names])}**
    
    Kategori-kategori ini terbukti memiliki:
    - ✅ Demand tinggi (total orders besar)
    - ✅ Revenue contribution signifikan ({top_5_pct:.1f}% dari total)
    - ✅ Impact langsung terhadap bottom line perusahaan
    
    **Rekomendasi Strategis:**
    
    1. **Inventory Optimization:** Pastikan stock availability untuk top 5 kategori selalu optimal
    2. **Marketing Focus:** Alokasi budget marketing terbesar untuk kategori dengan kontribusi revenue tertinggi
    3. **Cross-Selling:** Leverage kategori top performer untuk cross-sell produk dari kategori lain
    4. **Pricing Strategy:** Monitor AOV dan adjust pricing untuk maximize revenue dari kategori unggulan
    5. **Product Development:** Pertimbangkan ekspansi SKU dalam kategori high-performing
    """)

st.markdown("---")

# ===========================
# PERTANYAAN BISNIS 2
# ===========================
st.subheader("❓ Pertanyaan Bisnis 2: Metode Pembayaran Paling Sering Digunakan dan Nilai Transaksi Tertinggi")
st.markdown("**Metode pembayaran apa yang paling sering digunakan pelanggan dan memiliki nilai transaksi tertinggi selama periode 2016–2018?**")

tab3, tab4 = st.tabs(["📊 Visualisasi", "📋 Data"])

with tab3:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Frekuensi Penggunaan Metode Pembayaran")
        
        payment_freq = df_filtered['payment_type'].value_counts().reset_index()
        payment_freq.columns = ['payment_type', 'frequency']
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(range(len(payment_freq)), payment_freq['frequency'], 
                        color='#9b59b6', alpha=0.8)
        ax.set_xticks(range(len(payment_freq)))
        ax.set_xticklabels(payment_freq['payment_type'], rotation=45, ha='right')
        ax.set_xlabel('Metode Pembayaran', fontsize=12, fontweight='bold')
        ax.set_ylabel('Frekuensi (Jumlah Transaksi)', fontsize=12, fontweight='bold')
        ax.set_title('Frekuensi Penggunaan Metode Pembayaran', fontsize=14, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Tambahkan nilai dan persentase
        total_transactions = payment_freq['frequency'].sum()
        for i, (bar, row) in enumerate(zip(bars, payment_freq.itertuples())):
            value = row.frequency
            pct = (value / total_transactions) * 100
            ax.text(i, value, f'{value:,}\n({pct:.1f}%)', 
                   ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
    
    with col2:
        st.markdown("##### Total Pendapatan per Metode Pembayaran")
        
        payment_revenue = df_filtered.groupby('payment_type')['total_payment_value'].sum().reset_index()
        payment_revenue.columns = ['payment_type', 'total_revenue']
        payment_revenue = payment_revenue.sort_values('total_revenue', ascending=False)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(range(len(payment_revenue)), payment_revenue['total_revenue'], 
                        color='#e67e22', alpha=0.8)
        ax.set_xticks(range(len(payment_revenue)))
        ax.set_xticklabels(payment_revenue['payment_type'], rotation=45, ha='right')
        ax.set_xlabel('Metode Pembayaran', fontsize=12, fontweight='bold')
        ax.set_ylabel('Total Pendapatan (R$)', fontsize=12, fontweight='bold')
        ax.set_title('Total Pendapatan per Metode Pembayaran', fontsize=14, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Tambahkan nilai
        total_all = payment_revenue['total_revenue'].sum()
        for i, (bar, row) in enumerate(zip(bars, payment_revenue.itertuples())):
            value = row.total_revenue
            pct = (value / total_all) * 100
            ax.text(i, value, f'R$ {value/1000:.0f}K\n({pct:.1f}%)', 
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
    
    # Visualisasi gabungan
    st.markdown("##### Perbandingan Komprehensif: Frekuensi vs Pendapatan vs Rata-rata Nilai Transaksi")
    
    payment_analysis = df_filtered.groupby('payment_type').agg({
        'order_id': 'count',
        'total_payment_value': ['sum', 'mean']
    }).reset_index()
    payment_analysis.columns = ['payment_type', 'frequency', 'total_revenue', 'avg_transaction']
    payment_analysis = payment_analysis.sort_values('total_revenue', ascending=False)
    
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5))
    
    # Chart 1: Frequency
    bars1 = ax1.bar(payment_analysis['payment_type'], payment_analysis['frequency'], 
                    color='#3498db', alpha=0.8)
    ax1.set_xlabel('Metode Pembayaran', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Frekuensi', fontsize=11, fontweight='bold')
    ax1.set_title('Frekuensi Penggunaan', fontsize=12, fontweight='bold')
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, alpha=0.3, axis='y')
    for bar, value in zip(bars1, payment_analysis['frequency']):
        ax1.text(bar.get_x() + bar.get_width()/2, value, f'{value:,}', 
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Chart 2: Total Revenue
    bars2 = ax2.bar(payment_analysis['payment_type'], payment_analysis['total_revenue'], 
                color='#2ecc71', alpha=0.8)
    ax2.set_xlabel('Metode Pembayaran', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Total Pendapatan (R$)', fontsize=11, fontweight='bold')
    ax2.set_title('Total Pendapatan', fontsize=12, fontweight='bold')
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(True, alpha=0.3, axis='y')
    for bar, value in zip(bars2, payment_analysis['total_revenue']):
        ax2.text(bar.get_x() + bar.get_width()/2, value, f'R$ {value/1000:.0f}K', 
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Chart 3: Avg Transaction Value
    bars3 = ax3.bar(payment_analysis['payment_type'], payment_analysis['avg_transaction'], 
                    color='#e74c3c', alpha=0.8)
    ax3.set_xlabel('Metode Pembayaran', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Rata-rata Nilai Transaksi (R$)', fontsize=11, fontweight='bold')
    ax3.set_title('Rata-rata Nilai Transaksi', fontsize=12, fontweight='bold')
    ax3.tick_params(axis='x', rotation=45)
    ax3.grid(True, alpha=0.3, axis='y')
    for bar, value in zip(bars3, payment_analysis['avg_transaction']):
        ax3.text(bar.get_x() + bar.get_width()/2, value, f'R$ {value:.0f}', 
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

with tab4:
    st.markdown("##### Statistik Detail Metode Pembayaran")
    
    payment_stats = df_filtered.groupby('payment_type').agg({
        'order_id': 'count',
        'total_payment_value': ['sum', 'mean', 'median', 'std'],
        'max_installments': 'mean'
    }).round(2)
    payment_stats.columns = ['Total Transactions', 'Total Revenue (R$)', 'Avg Transaction (R$)', 
                            'Median Transaction (R$)', 'Std Transaction (R$)', 'Avg Installments']
    
    # Tambahkan persentase
    payment_stats['Transaction Share (%)'] = (payment_stats['Total Transactions'] / 
                                              payment_stats['Total Transactions'].sum() * 100).round(2)
    payment_stats['Revenue Share (%)'] = (payment_stats['Total Revenue (R$)'] / 
                                          payment_stats['Total Revenue (R$)'].sum() * 100).round(2)
    
    payment_stats = payment_stats.sort_values('Total Revenue (R$)', ascending=False)
    st.dataframe(payment_stats, use_container_width=True)
    
    # Summary
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        most_used = payment_freq.iloc[0]['payment_type']
        st.metric("Metode Paling Sering", most_used)
    with col_p2:
        highest_revenue = payment_revenue.iloc[0]['payment_type']
        st.metric("Pendapatan Tertinggi", highest_revenue)
    with col_p3:
        highest_avg = payment_analysis.sort_values('avg_transaction', ascending=False).iloc[0]['payment_type']
        st.metric("Rata-rata Nilai Transaksi Tertinggi", highest_avg)

with st.expander("💡 Insight & Kesimpulan"):
    most_freq_method = payment_freq.iloc[0]['payment_type']
    most_freq_count = payment_freq.iloc[0]['frequency']
    most_freq_pct = (most_freq_count / payment_freq['frequency'].sum()) * 100
    
    highest_rev_method = payment_revenue.iloc[0]['payment_type']
    highest_rev_value = payment_revenue.iloc[0]['total_revenue']
    highest_rev_pct = (highest_rev_value / payment_revenue['total_revenue'].sum()) * 100
    
    highest_avg_method = payment_analysis.sort_values('avg_transaction', ascending=False).iloc[0]['payment_type']
    highest_avg_value = payment_analysis.sort_values('avg_transaction', ascending=False).iloc[0]['avg_transaction']
    
    st.write(f"""
    **Temuan Utama:**
    - Metode pembayaran **{most_freq_method}** adalah yang paling sering digunakan dengan **{most_freq_count:,} transaksi** ({most_freq_pct:.1f}%)
    - Metode **{highest_rev_method}** menghasilkan revenue tertinggi sebesar **R$ {highest_rev_value:,.2f}** ({highest_rev_pct:.1f}% dari total revenue)
    - Metode **{highest_avg_method}** memiliki nilai transaksi rata-rata tertinggi sebesar **R$ {highest_avg_value:,.2f}**
    
    **Kesimpulan:**
    Metode pembayaran {most_freq_method} mendominasi baik dari segi frekuensi penggunaan maupun kontribusi revenue. 
    Perusahaan sebaiknya memastikan infrastruktur payment gateway untuk metode ini selalu optimal dan mempertimbangkan 
    program insentif untuk metode pembayaran lain guna mendiversifikasi opsi pembayaran pelanggan.
    """)

st.markdown("---")

# ===========================
# PERTANYAAN BISNIS 3: RFM ANALYSIS
# ===========================
st.subheader("❓ Pertanyaan Bisnis 3: Segmentasi Pelanggan Berdasarkan RFM Analysis")
st.markdown("**Bagaimana segmentasi pelanggan E-Commerce berdasarkan Recency, Frequency, dan Monetary (RFM) selama periode 2016–2018, serta segmen pelanggan mana yang memberikan kontribusi pendapatan terbesar?**")

# Hitung RFM
@st.cache_data
def calculate_rfm(df_input):
    # Tentukan tanggal analisis
    snapshot_date = df_input['order_purchase_timestamp'].max() + pd.Timedelta(days=1)
    
    rfm = df_input.groupby('customer_unique_id').agg({
        'order_purchase_timestamp': lambda x: (snapshot_date - x.max()).days,  # Recency
        'order_id': 'count',  # Frequency
        'total_payment_value': 'sum'  # Monetary
    }).reset_index()
    
    rfm.columns = ['customer_id', 'recency', 'frequency', 'monetary']
    
    # Buat scoring 
    rfm['r_score'] = pd.qcut(rfm['recency'], q=5, labels=[5, 4, 3, 2, 1], duplicates='drop')
    rfm['f_score'] = pd.qcut(rfm['frequency'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5], duplicates='drop')
    rfm['m_score'] = pd.qcut(rfm['monetary'], q=5, labels=[1, 2, 3, 4, 5], duplicates='drop')
    
    # Gabungkan score
    rfm['rfm_score'] = rfm['r_score'].astype(str) + rfm['f_score'].astype(str) + rfm['m_score'].astype(str)
    rfm['rfm_score_sum'] = rfm['r_score'].astype(int) + rfm['f_score'].astype(int) + rfm['m_score'].astype(int)
    
    # Segmentasi
    def segment_customer(row):
        r, f, m = int(row['r_score']), int(row['f_score']), int(row['m_score'])
        
        if r >= 4 and f >= 4 and m >= 4:
            return 'Champions'
        elif r >= 3 and f >= 3 and m >= 3:
            return 'Loyal Customers'
        elif r >= 4 and f <= 2:
            return 'Promising'
        elif r >= 3 and f <= 2 and m <= 2:
            return 'New Customers'
        elif r <= 2 and f >= 3 and m >= 3:
            return 'At Risk'
        elif r <= 2 and f <= 2 and m >= 3:
            return 'Cant Lose Them'
        elif r <= 2 and f >= 2 and m <= 2:
            return 'Hibernating'
        else:
            return 'Lost'
    
    rfm['segment'] = rfm.apply(segment_customer, axis=1)
    
    return rfm

rfm_data = calculate_rfm(df_filtered)

tab5, tab6, tab7 = st.tabs(["📊 Visualisasi Segmentasi", "📈 Analisis RFM", "📋 Data"])

with tab5:
    st.markdown("##### Distribusi Customer Segmentation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart distribusi segmen
        segment_dist = rfm_data['segment'].value_counts()
        
        fig, ax = plt.subplots(figsize=(10, 8))
        colors_seg = ['#2ecc71', '#3498db', '#f39c12', '#9b59b6', '#e74c3c', '#1abc9c', '#e67e22', '#95a5a6']
        wedges, texts, autotexts = ax.pie(
            segment_dist.values,
            labels=segment_dist.index,
            autopct='%1.1f%%',
            colors=colors_seg,
            startangle=90,
            textprops={'fontsize': 10}
        )
        ax.set_title('Customer Segmentation Distribution', fontsize=14, fontweight='bold', pad=20)
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
    
    with col2:
        # Bar chart jumlah customer per segmen
        fig, ax = plt.subplots(figsize=(10, 8))
        bars = ax.barh(range(len(segment_dist)), segment_dist.values, color=colors_seg, alpha=0.8)
        ax.set_yticks(range(len(segment_dist)))
        ax.set_yticklabels(segment_dist.index)
        ax.set_xlabel('Jumlah Customer', fontsize=12, fontweight='bold')
        ax.set_ylabel('Customer Segment', fontsize=12, fontweight='bold')
        ax.set_title('Jumlah Customer per Segmen', fontsize=14, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3, axis='x')
        
        for i, (bar, value) in enumerate(zip(bars, segment_dist.values)):
            pct = (value / segment_dist.sum()) * 100
            ax.text(value, i, f' {value:,} ({pct:.1f}%)', va='center', fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
    
    # Revenue contribution per segment
    st.markdown("##### Kontribusi Pendapatan per Segmen Customer")
    
    segment_revenue = rfm_data.groupby('segment').agg({
        'monetary': 'sum',
        'customer_id': 'count',
        'frequency': 'sum'
    }).reset_index()
    segment_revenue.columns = ['segment', 'total_revenue', 'customer_count', 'total_orders']
    segment_revenue = segment_revenue.sort_values('total_revenue', ascending=False)
    
    col_rev1, col_rev2 = st.columns(2)
    
    with col_rev1:
        fig, ax = plt.subplots(figsize=(12, 6))
        bars = ax.bar(range(len(segment_revenue)), segment_revenue['total_revenue'], 
                        color=colors_seg, alpha=0.8)
        ax.set_xticks(range(len(segment_revenue)))
        ax.set_xticklabels(segment_revenue['segment'], rotation=45, ha='right')
        ax.set_xlabel('Customer Segment', fontsize=12, fontweight='bold')
        ax.set_ylabel('Total Pendapatan (R$)', fontsize=12, fontweight='bold')
        ax.set_title('Total Pendapatan per Segmen Customer', fontsize=14, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3, axis='y')
        
        total_rfm_revenue = segment_revenue['total_revenue'].sum()
        for i, (bar, row) in enumerate(zip(bars, segment_revenue.itertuples())):
            value = row.total_revenue
            pct = (value / total_rfm_revenue) * 100
            ax.text(i, value, f'R$ {value/1000:.0f}K\n({pct:.1f}%)', 
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
    
    with col_rev2:
        # Average revenue per customer per segment
        segment_revenue['avg_revenue_per_customer'] = segment_revenue['total_revenue'] / segment_revenue['customer_count']
        
        fig, ax = plt.subplots(figsize=(12, 6))
        bars = ax.bar(range(len(segment_revenue)), segment_revenue['avg_revenue_per_customer'], 
                        color=colors_seg, alpha=0.8)
        ax.set_xticks(range(len(segment_revenue)))
        ax.set_xticklabels(segment_revenue['segment'], rotation=45, ha='right')
        ax.set_xlabel('Customer Segment', fontsize=12, fontweight='bold')
        ax.set_ylabel('Rata-rata Pendapatan per Customer (R$)', fontsize=12, fontweight='bold')
        ax.set_title('Rata-rata Pendapatan per Customer berdasarkan Segmen', fontsize=14, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3, axis='y')
        
        for i, (bar, value) in enumerate(zip(bars, segment_revenue['avg_revenue_per_customer'])):
            ax.text(i, value, f'R$ {value:.0f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

with tab6:
    st.markdown("##### Analisis RFM Metrics")
    
    col_rfm1, col_rfm2, col_rfm3 = st.columns(3)
    
    with col_rfm1:
        st.markdown("**Recency Distribution**")
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.hist(rfm_data['recency'], bins=30, color='#3498db', alpha=0.7, edgecolor='black')
        ax.set_xlabel('Recency (days)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Frequency', fontsize=11, fontweight='bold')
        ax.set_title('Distribution of Recency', fontsize=12, fontweight='bold')
        ax.axvline(rfm_data['recency'].median(), color='red', linestyle='--', linewidth=2, label=f'Median: {rfm_data["recency"].median():.0f} days')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
        
        st.metric("Avg Recency", f"{rfm_data['recency'].mean():.0f} days")
        st.metric("Median Recency", f"{rfm_data['recency'].median():.0f} days")
    
    with col_rfm2:
        st.markdown("**Frequency Distribution**")
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.hist(rfm_data['frequency'], bins=30, color='#2ecc71', alpha=0.7, edgecolor='black')
        ax.set_xlabel('Frequency (orders)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Count', fontsize=11, fontweight='bold')
        ax.set_title('Distribution of Frequency', fontsize=12, fontweight='bold')
        ax.axvline(rfm_data['frequency'].median(), color='red', linestyle='--', linewidth=2, label=f'Median: {rfm_data["frequency"].median():.0f} orders')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
        
        st.metric("Avg Frequency", f"{rfm_data['frequency'].mean():.2f} orders")
        st.metric("Median Frequency", f"{rfm_data['frequency'].median():.0f} orders")
    
    with col_rfm3:
        st.markdown("**Monetary Distribution**")
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.hist(rfm_data['monetary'], bins=30, color='#e74c3c', alpha=0.7, edgecolor='black')
        ax.set_xlabel('Monetary (R$)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Count', fontsize=11, fontweight='bold')
        ax.set_title('Distribution of Monetary Value', fontsize=12, fontweight='bold')
        ax.axvline(rfm_data['monetary'].median(), color='blue', linestyle='--', linewidth=2, label=f'Median: R$ {rfm_data["monetary"].median():.0f}')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
        
        st.metric("Avg Monetary", f"R$ {rfm_data['monetary'].mean():.2f}")
        st.metric("Median Monetary", f"R$ {rfm_data['monetary'].median():.2f}")
    
    # Scatter plots
    st.markdown("##### Hubungan antar RFM Metrics")
    
    col_scatter1, col_scatter2 = st.columns(2)
    
    with col_scatter1:
        fig, ax = plt.subplots(figsize=(10, 6))
        scatter = ax.scatter(rfm_data['frequency'], rfm_data['monetary'], 
                            c=rfm_data['recency'], cmap='viridis', alpha=0.6, s=50)
        ax.set_xlabel('Frequency (orders)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Monetary (R$)', fontsize=12, fontweight='bold')
        ax.set_title('Frequency vs Monetary (colored by Recency)', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3)
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Recency (days)', fontsize=11)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
    
    with col_scatter2:
        fig, ax = plt.subplots(figsize=(10, 6))
        scatter = ax.scatter(rfm_data['recency'], rfm_data['monetary'], 
                            c=rfm_data['frequency'], cmap='plasma', alpha=0.6, s=50)
        ax.set_xlabel('Recency (days)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Monetary (R$)', fontsize=12, fontweight='bold')
        ax.set_title('Recency vs Monetary (colored by Frequency)', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3)
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Frequency (orders)', fontsize=11)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

with tab7:
    st.markdown("##### Statistik Detail per Segmen Customer")
    
    segment_stats = rfm_data.groupby('segment').agg({
        'customer_id': 'count',
        'recency': ['mean', 'median'],
        'frequency': ['mean', 'median', 'sum'],
        'monetary': ['mean', 'median', 'sum']
    }).round(2)
    
    segment_stats.columns = ['Customer Count', 'Avg Recency', 'Median Recency', 
                            'Avg Frequency', 'Median Frequency', 'Total Orders',
                            'Avg Monetary', 'Median Monetary', 'Total Revenue']
    
    # Tambahkan persentase
    segment_stats['Customer %'] = (segment_stats['Customer Count'] / segment_stats['Customer Count'].sum() * 100).round(2)
    segment_stats['Revenue %'] = (segment_stats['Total Revenue'] / segment_stats['Total Revenue'].sum() * 100).round(2)
    
    segment_stats = segment_stats.sort_values('Total Revenue', ascending=False)
    st.dataframe(segment_stats, use_container_width=True)
    
    # Top segment summary
    col_seg1, col_seg2, col_seg3, col_seg4 = st.columns(4)
    
    top_segment = segment_stats.index[0]
    with col_seg1:
        st.metric("Segmen dengan Pendapatan Tertinggi", top_segment)
    with col_seg2:
        top_revenue = segment_stats.loc[top_segment, 'Total Revenue']
        st.metric("Pendapatan Segmen Teratas", f"R$ {top_revenue:,.2f}")
    with col_seg3:
        top_pct = segment_stats.loc[top_segment, 'Revenue %']
        st.metric("Kontribusi Pendapatan", f"{top_pct:.1f}%")
    with col_seg4:
        top_customers = segment_stats.loc[top_segment, 'Customer Count']
        st.metric("Jumlah Customer", f"{int(top_customers):,}")

with st.expander("💡 Insight & Kesimpulan"):
    top_seg_name = segment_stats.index[0]
    top_seg_revenue = segment_stats.loc[top_seg_name, 'Total Pendapatan']
    top_seg_pct = segment_stats.loc[top_seg_name, 'Pendapatan %']
    top_seg_customers = int(segment_stats.loc[top_seg_name, 'Customer Count'])
    top_seg_avg_monetary = segment_stats.loc[top_seg_name, 'Avg Monetary']
    
    champions_count = int(segment_stats.loc['Champions', 'Customer Count']) if 'Champions' in segment_stats.index else 0
    champions_revenue = segment_stats.loc['Champions', 'Total Pendapatan'] if 'Champions' in segment_stats.index else 0
    
    st.write(f"""
    **Temuan Utama:**
    - Segmen **{top_seg_name}** memberikan kontribusi pendapatan terbesar dengan total **R$ {top_seg_revenue:,.2f}** atau **{top_seg_pct:.1f}%** dari total pendapatan
    - Terdapat **{top_seg_customers:,} customers** di segmen {top_seg_name} dengan rata-rata nilai belanja **R$ {top_seg_avg_monetary:,.2f}**
    - Segmen **Champions** (customer terbaik) terdiri dari **{champions_count:,} customers** yang berkontribusi **R$ {champions_revenue:,.2f}**
    - Customer dengan recency rendah (baru bertransaksi) dan frequency tinggi menunjukkan loyalitas yang baik
    
    **Rekomendasi Strategi:**
    1. **Champions & Loyal Customers**: Pertahankan dengan program loyalitas premium, early access, dan exclusive benefits
    2. **Promising**: Nurture dengan email marketing dan special offers untuk meningkatkan frequency
    3. **At Risk & Cant Lose Them**: Win-back campaign dengan discount dan personalized recommendations
    4. **Hibernating & Lost**: Reactivation campaign dengan incentive besar atau survey untuk memahami alasan churn
    
    **Kesimpulan:**
    Fokus retention pada segmen {top_seg_name} dan Champions sangat critical karena memberikan kontribusi pendapatan terbesar. 
    Implementasi strategi marketing yang terpersonalisasi per segmen akan memaksimalkan customer lifetime value (CLV).
    """)

# ===========================
# FOOTER
# ===========================
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>📊 Dashboard Analisis E-Commerce | Periode 2016-2018</p>
        <p>Dibuat dengan ❤️ menggunakan Streamlit | © 2024</p>
    </div>
""", unsafe_allow_html=True)