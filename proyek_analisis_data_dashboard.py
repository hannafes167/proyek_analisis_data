# Prepare library 
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
sns.set(style='dark')

# Create Data Frame
def create_daily_orders_df(df):
    daily_orders_df = ecommerce_all_df.resample(rule='D', on="order_purchase_timestamp").agg({
    "order_id": "nunique",
    "revenue": "sum"
    }).reset_index()

    daily_orders_df.rename(columns={
        "order_id": "order_count",
    }, inplace=True)

    return daily_orders_df

def create_product_sales_df(df):
    product_sales = ecommerce_all_df.groupby(by="product_category_name_english").order_item_id.sum().sort_values(ascending=False).reset_index()
    return product_sales

def create_customers_city_df(df):
    customers_city = ecommerce_all_df.groupby(by="customer_city").customer_unique_id.nunique().sort_values(ascending=False).reset_index()
    return customers_city

def create_city_sales_df(df):
    city_sales = ecommerce_all_df.groupby(by="seller_city").order_item_id.sum().sort_values(ascending=False).reset_index()
    return city_sales

def create_rfm_df(df):
    rfm_df = ecommerce_all_df.groupby(by="customer_id", as_index=False).agg({
    "order_purchase_timestamp" : "max",
    "order_id": "nunique",
    "revenue": "sum"
    })
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = ecommerce_all_df["order_purchase_timestamp"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    
    return rfm_df

ecommerce_all_df = pd.read_csv("https://docs.google.com/spreadsheets/d/1OlTpzuQNptGwyQV162ZBpyTSAhmNOxVvIEERZ1sj34I/edit?usp=sharing.csv")

# Convert to datetime before sorting
ecommerce_all_df["order_purchase_timestamp"] = pd.to_datetime(ecommerce_all_df["order_purchase_timestamp"])

# Set index to order_purchase_timestamp before resample
ecommerce_all_df.set_index("order_purchase_timestamp", inplace=True)
datetime_columns = ["order_purchase_timestamp", "order_delivered_customer_date"]
ecommerce_all_df.sort_values(by="order_purchase_timestamp", inplace=True)
ecommerce_all_df.reset_index(inplace=True)

# Create Filter
min_date = ecommerce_all_df["order_purchase_timestamp"].min()
max_date = ecommerce_all_df["order_purchase_timestamp"].max()

with st.sidebar:
    #add logo
    st.image("https://w7.pngwing.com/pngs/621/196/png-transparent-e-commerce-logo-logo-e-commerce-electronic-business-ecommerce-angle-text-service-thumbnail.png")

    #take start_date & end_date from data input
    start_date, end_date = st.date_input(
        label='Range Time', min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

main_df = ecommerce_all_df[(ecommerce_all_df["order_purchase_timestamp"] >= str(start_date)) & (ecommerce_all_df["order_purchase_timestamp"] <= str(end_date))] 

daily_orders_df = create_daily_orders_df(main_df)
product_sales = create_product_sales_df(main_df)
customers_city = create_customers_city_df(main_df)
city_sales = create_city_sales_df(main_df)
rfm_df = create_rfm_df(main_df)

# Build Dashboard with all visualization
st.header('E-Commerce Public')

# Daily Orders
st.subheader('Daily Orders')

col1, col2 = st.columns(2)

with col1:
    total_orders = daily_orders_df.order_count.sum()
    st.metric("Sales Trends", value=total_orders)

with col2:
    total_revenue = daily_orders_df.revenue.sum()
    st.metric("Revenue Trends", value=total_revenue)

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    daily_orders_df["order_purchase_timestamp"],
    daily_orders_df["order_count"],
    marker='o',
    linewidth=2,
    color="#90CAF9"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)

st.pyplot(fig)

# Best and Worst Product Selling
best_selling = product_sales.sort_values(by="order_item_id", ascending=False).head(5)
worst_selling = product_sales.sort_values(by="order_item_id", ascending=True).head(5)

st.subheader("Best and Worst Selling Product")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35, 15))

colors = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(x="order_item_id", y="product_category_name_english", data=best_selling, palette=colors, ax=ax[0])
ax[0].set_ylabel("Product Name", fontsize=30)
ax[0].set_xlabel("Total Quantity Sold", fontsize=30)
ax[0].set_title("Best Selling Product", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=30)
ax[0].tick_params(axis='x', labelsize=30)

sns.barplot(x="order_item_id", y="product_category_name_english", data=worst_selling, palette=colors, ax=ax[1])
ax[1].set_ylabel("")
ax[1].set_xlabel("Total Quantity Sold", fontsize=30)
ax[1].set_title("Worst Selling Product", loc="center", fontsize=50)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].tick_params(axis='y', labelsize=30)
ax[1].tick_params(axis='x', labelsize=30)
st.pyplot(fig)

st.subheader("Top Customers and Sellers by City")
col1, col2 = st.columns(2)
# Demographi customer by city
with col1:
    fig, ax = plt.subplots(figsize=(20, 10))
    
    sns.barplot(
        y="customer_unique_id",
        x="customer_city",
        data=customers_city.head(5),
        palette=colors
        )

    ax.set_title("Top Customers by City", loc="center", fontsize=50)
    ax.set_ylabel("Customer Count", fontsize=30)
    ax.set_xlabel("City", fontsize=30)
    ax.tick_params(axis='y', labelsize=30)
    ax.tick_params(axis='x', labelsize=30)
    st.pyplot(fig)

#Top sellers by City
with col2:
    fig, ax = plt.subplots(figsize=(20, 10))
    
    sns.barplot(
        y="order_item_id",
        x="seller_city",
        data=city_sales.head(5),
        palette=colors
        )
    
    ax.set_title("Top Sellers by City", loc="center", fontsize=50)
    ax.set_ylabel("Seller Count", fontsize=30)
    ax.set_xlabel("City", fontsize=30)
    ax.tick_params(axis='y', labelsize=30)
    ax.tick_params(axis='x', labelsize=30)
    st.pyplot(fig)

# rfm
st.subheader("Best Customer Based on RFM Parameters (customer_id)")
rfm_df["customer_id_short"] = rfm_df["customer_id"].str[:6]
fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))

colors = ["#72BCD4", "#72BCD4", "#72BCD4", "#72BCD4", "#72BCD4"]

sns.barplot(y="recency", x="customer_id_short", data=rfm_df.sort_values(by="recency", ascending=True).head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel(None)
ax[0].set_title("By Recency (days)", loc="center", fontsize=50)
ax[0].tick_params(axis ='x', labelsize=20)
ax[0].tick_params(axis='y', labelsize=30)
 
sns.barplot(y="frequency", x="customer_id_short", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel(None)
ax[1].set_title("By Frequency", loc="center", fontsize=50)
ax[1].tick_params(axis='x', labelsize=20)
ax[1].tick_params(axis='y', labelsize=30)
 
sns.barplot(y="monetary", x="customer_id_short", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
ax[2].set_ylabel(None)
ax[2].set_xlabel(None)
ax[2].set_title("By Monetary", loc="center", fontsize=50)
ax[2].tick_params(axis='x', labelsize=20)
ax[2].tick_params(axis='y', labelsize=30)
 
st.pyplot(fig)
