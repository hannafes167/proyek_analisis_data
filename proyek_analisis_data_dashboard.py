# Import Library
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
sns.set(style='dark')

# Data Frame
def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule='D', on="order_purchase_timestamp").agg({
        "order_id": "nunique",
        "revenue": "sum"
    }).reset_index()

    daily_orders_df.rename(columns={
        "order_id": "order_count",
    }, inplace=True)
    
    daily_orders_df['order_purchase_timestamp'] = pd.to_datetime(daily_orders_df['order_purchase_timestamp'])
    return daily_orders_df

def create_product_sales_df(df):
    product_sales = df.groupby(by="product_category_name_english").order_item_id.sum().sort_values(ascending=False).reset_index()
    return product_sales

def create_customers_city_df(df):
    customers_city = df.groupby(by="customer_city").customer_unique_id.nunique().sort_values(ascending=False).reset_index()
    return customers_city

def create_city_sales_df(df):
    city_sales = df.groupby(by="seller_city").order_item_id.sum().sort_values(ascending=False).reset_index()
    return city_sales

def create_rfm_df(df):
    rfm_df = df.groupby(by="customer_id", as_index=False).agg({
        "order_purchase_timestamp": "max",
        "order_id": "nunique",
        "revenue": "sum"
    })
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_purchase_timestamp"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    return rfm_df

# Load data
@st.cache_data
def load_data():
    url = "https://drive.google.com/uc?export=download&id=1z9fAU2MpEFKMydxVWuSUOAa1J3vM9k-m"
    df = pd.read_csv(url)
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    return df
ecommerce_all_df = load_data()

# Data preparation
min_date = ecommerce_all_df["order_purchase_timestamp"].min().date()
max_date = ecommerce_all_df["order_purchase_timestamp"].max().date()

# Side bar
with st.sidebar:
    st.image("https://w7.pngwing.com/pngs/621/196/png-transparent-e-commerce-logo-logo-e-commerce-electronic-business-ecommerce-angle-text-service-thumbnail.png")
    
    try:
        # filter date
        start_date, end_date = st.date_input(
            label='Range Time', 
            min_value=min_date,
            max_value=max_date,
            value=[min_date, max_date]
        )

        if isinstance(start_date, tuple) or isinstance(end_date, tuple):
            start_date, end_date = min_date, max_date
            st.warning("Please select both start and end dates. Using full range instead.")
            
    except Exception as e:
        st.error(f"Error setting date range: {str(e)}")
        start_date, end_date = min_date, max_date

    # filter product and city    
    selected_category = st.selectbox(
        label='Product Category',
        options=['All'] + list(ecommerce_all_df["product_category_name_english"].unique()))
    
    selected_city = st.selectbox(
        label='City', 
        options=['All'] + list(ecommerce_all_df["seller_city"].unique()))

# Filter main dataframe by date first
main_df = ecommerce_all_df[
    (ecommerce_all_df["order_purchase_timestamp"].dt.date >= start_date) & 
    (ecommerce_all_df["order_purchase_timestamp"].dt.date <= end_date)
]

# Filter main dataframe by produdt and city
if selected_category != 'All':
    main_df = main_df[main_df["product_category_name_english"] == selected_category]

if selected_city != 'All':
    main_df = main_df[main_df["seller_city"] == selected_city]


# If DataFrame is empty 
if main_df.empty:
    st.error(f"No orders found for:")
    if selected_category != 'All':
        st.write(f"- Category: {selected_category}")
    if selected_city != 'All':
        st.write(f"- City: {selected_city}")
    st.write(f"Date range: {start_date} to {end_date}")
    st.stop()

# Visualizations
daily_orders_df = create_daily_orders_df(main_df)
product_sales = create_product_sales_df(main_df)
customers_city = create_customers_city_df(main_df)
city_sales = create_city_sales_df(main_df)
rfm_df = create_rfm_df(main_df)

# Data Visualization
color_scale = px.colors.sequential.Reds
st.header('E-Commerce Public')

# Daily Orders
try: 
    st.subheader('Daily Orders')
    col1, col2 = st.columns(2)
    with col1:
        total_orders = daily_orders_df.order_count.sum()
        st.metric("Sales Trends", value=total_orders)
    with col2:
        total_revenue = daily_orders_df.revenue.sum()
        st.metric("Revenue Trends", value=total_revenue)
    
    fig = px.line(daily_orders_df, 
                 x="order_purchase_timestamp", 
                 y="order_count",
                 title="Daily Order Trends",
                 labels={"order_count": "Number of Orders", "order_purchase_timestamp": "Date"},
                 template="plotly_white")
    
    fig.update_traces(line=dict(color="#800000", width=2.5),
                     marker=dict(size=8, color="#800000"))
    fig.update_layout(hovermode="x unified",
                     xaxis_title="Date",
                     yaxis_title="Orders",
                     height=500)
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))

    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error creating daily orders chart: {str(e)}")

# Best and Worst Product Selling
try:
    COLOR_SCALES =  ["#800000", "#FFF5EE", "#FFF5EE", "#FFF5EE", "#FFF5EE"]
    best_selling = product_sales.sort_values(by="order_item_id", ascending=False).head(5)
    worst_selling = product_sales.sort_values(by="order_item_id", ascending=True).head(5)
    st.subheader("Best and Worst Selling Product")
    fig = make_subplots(rows=1, cols=2, 
                        subplot_titles=("Best Selling Products", "Worst Selling Products"),
                        horizontal_spacing=0.4)
    
    # Best selling
    fig.add_trace(
        go.Bar(y=best_selling["product_category_name_english"],
               x=best_selling["order_item_id"],
               orientation='h',
               marker_color=COLOR_SCALES,
               name="Best Sellers"),
        row=1, col=1
    )
    
    # Worst selling (inverted)
    fig.add_trace(
        go.Bar(y=worst_selling["product_category_name_english"],
               x=worst_selling["order_item_id"],
               orientation='h',
               marker_color=COLOR_SCALES,
               name="Worst Sellers"),
        row=1, col=2
    )
    
    fig.update_layout(height=600, showlegend=False,
                     hovermode="closest")
    fig.update_xaxes(title_text="Quantity Sold", row=1, col=1)
    fig.update_yaxes(autorange="reversed", row=1, col=2)  
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))

    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error creating product sales chart: {str(e)}")

# Demography customer and top sellers by city
try: 
    COLOR_SCALES =  ["#800000", "#FFF5EE", "#FFF5EE", "#FFF5EE", "#FFF5EE"]
    st.subheader("Top Customers and Sellers by City")
    tab1, tab2 = st.tabs(["Top Customers by City", "Top Sellers by City"])
    
    with tab1:
        fig = px.bar(customers_city.head(5),
                     x="customer_city",
                     y="customer_unique_id",
                     color_discrete_sequence=COLOR_SCALES,
                     title="Top Customer Cities",
                     labels={"customer_unique_id": "Customer Count", "customer_city": "City"})
        fig.update_layout(hovermode="x")
        fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        fig = px.bar(city_sales.head(5),
                     x="seller_city",
                     y="order_item_id",
                     color_discrete_sequence=COLOR_SCALES,
                     title="Top Seller Cities",
                     labels={"order_item_id": "Items Sold", "seller_city": "City"})
        fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error creating Top Customers and Sellers by City chart: {str(e)}")

# rfm
try:
    MAROON_SCALES =  ["#FFF5EE", "#800000"]  
    
    st.subheader("Best Customer Based on RFM Parameters (customer_id)")
    rfm_df["customer_id_short"] = rfm_df["customer_id"].str[:6]
    
    tab1, tab2, tab3 = st.tabs(["🕒 Recency (Recent Customers)", "🔄 Frequency (Loyal Customers)", "💰 Monetary (Big Spenders)"])
    
    with tab1:
        fig = px.bar(rfm_df.sort_values("recency").head(5),
                     x="customer_id_short",
                     y="recency",
                     title="Top Customers by Recency (Days Since Last Purchase)",
                     color="recency",
                     color_continuous_scale=MAROON_SCALES)
        fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        fig = px.bar(
            rfm_df.sort_values("frequency", ascending=False).head(5),
            x="customer_id_short",
            y="frequency",
            title="Top Customers by Order Frequency",
            color="frequency",
            color_continuous_scale=MAROON_SCALES)
        
        fig.update_layout(xaxis={'type': 'category'},  
            uniformtext_minsize=8,
            margin=dict(l=50, r=50, t=80, b=50)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        fig = px.bar(rfm_df.sort_values("monetary", ascending=False).head(5),
                     x="customer_id_short",
                     y="monetary",
                     title="Top Customers by Spending (Monetary)",
                     color="monetary",
                     color_continuous_scale=MAROON_SCALES)
        fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error creating Best Customer Based on RFM Parameters (customer_id) chart: {str(e)}")
