# 订单销售管理技能 (Order Sales Management Skill)

## 技能描述
本技能用于订单销售管理系统的智能客服，支持通过自然语言操作订单、产品、供应商相关的 API 接口。

## API 基础信息
- **Base URL**: `http://121.43.198.13:8080`
- **Content-Type**: `application/json`
- **认证方式**: `X-API-Key` Header

---

## 一、订单管理接口 (Order)

### 1. 创建订单
- **POST** `/orders/createOrder`
- **参数**: `{ quantity: int, supplierId: int, productId: int, orderRegion: string }`
- **说明**: 创建新订单，需要提供产品ID、数量、物流供应商ID、配送区域

### 2. 查询订单详情
- **POST** `/orders/getOrderByOrderId`
- **参数**: `{ orderId: int }`
- **说明**: 根据订单ID查询订单详情，包含物流供应商信息

### 3. 更新订单状态
- **PUT** `/orders/updateOrderStatus`
- **参数**: `{ orderId: int, newStatus: string }`
- **说明**: 更新订单状态（如：待处理、运输中、已送达、已取消等）

### 4. 取消订单
- **DELETE** `/orders/cancelOrder`
- **参数**: `{ orderId: int }`
- **说明**: 根据订单ID取消订单

### 5. 按状态查询订单
- **POST** `/orders/getByOrderStatus`
- **参数**: `{ status: string }`
- **说明**: 查询特定状态的所有订单

### 6. 按产品查询订单
- **POST** `/orders/getByProductId`
- **参数**: `{ productId: int }`
- **说明**: 查询特定产品的所有订单

### 7. 按时间范围查询订单
- **POST** `/orders/getByTimeRange`
- **参数**: `{ startDate: datetime, endDate: datetime }`
- **说明**: 查询特定时间范围内的订单

### 8. 按供应商查询订单
- **POST** `/orders/getOrdersBySupplierId`
- **参数**: `{ supplierId: int }`
- **说明**: 查询某个物流供应商配送的所有订单

---

## 二、产品管理接口 (Product)

### 1. 按ID查询产品
- **POST** `/products/getProductById`
- **参数**: `{ productId: int }`
- **返回**: 产品ID、名称、描述、价格、库存量、替代产品ID

### 2. 按名称查询产品
- **POST** `/products/getProductByName`
- **参数**: `{ name: string }`
- **说明**: 按产品名称模糊查询，如"苹果"、"有机西兰花"

### 3. 批量查询产品
- **POST** `/products/getBatchProductByProductIds`
- **参数**: `{ startId: int, endId: int }`
- **说明**: 按ID范围批量获取产品信息

### 4. 添加产品
- **POST** `/products/addProduct`
- **参数**: `{ name: string, description: string, price: float, quantityInStock: int }`

### 5. 更新产品描述
- **POST** `/products/updateProductDescription`
- **参数**: `{ productId: int, description: string }`

### 6. 按ID删除产品
- **DELETE** `/products/removeProductById`
- **参数**: `{ productId: int }`

### 7. 按名称删除产品
- **DELETE** `/products/removeProductByName`
- **参数**: `{ name: string }`

### 8. 查询替代产品（按ID）
- **POST** `/products/getProductSubstitutes`
- **参数**: `{ productId: int }`

### 9. 查询替代产品（按名称）
- **POST** `/products/getProductSubstitutesByName`
- **参数**: `{ name: string }`
- **说明**: 当某产品库存不足时，查询可推荐的替代品

### 10. 更新替代产品
- **POST** `/products/updateProductSubstitutes`
- **参数**: `{ productId: int, substituteName: string }`

---

## 三、供应商管理接口 (Supplier)

### 1. 按ID查询供应商
- **GET** `/suppliers/getSupplierById/{supplierId}`

### 2. 按名称查询供应商
- **GET** `/suppliers/getSupplierByName?supplierName={name}`

### 3. 按状态查询供应商
- **GET** `/suppliers/getSupplierByStatus?status=InUse|DisUse`
- **说明**: 按评分高低排序返回供应商列表

### 4. 按配送区域查询供应商
- **POST** `/suppliers/querySuppliersByDeliveryRegion`
- **参数**: `{ region: string }`

### 5. 添加供应商
- **POST** `/suppliers/addSuppliers`
- **参数**: `{ name: string, phone: string, address: string, deliveryAreas: string[], rating: float, status: "InUse"|"DisUse" }`

### 6. 按ID删除供应商
- **DELETE** `/suppliers/deleteSupplierById`
- **参数**: `{ id: int }`

### 7. 按名称删除供应商
- **DELETE** `/suppliers/deleteSupplierByName`
- **参数**: `{ name: string }`

---

## 四、常见业务流程

### 创建订单流程
1. 先查询产品信息（getProductByName）确认产品和库存
2. 如果库存不足，查询替代产品（getProductSubstitutesByName）
3. 查询配送区域的供应商（querySuppliersByDeliveryRegion）
4. 创建订单（createOrder）

### 订单状态管理流程
1. 查询订单详情（getOrderByOrderId）
2. 根据需要更新状态（updateOrderStatus）
3. 如需取消，调用取消接口（cancelOrder）

### 库存不足处理流程
1. 查询产品信息确认库存
2. 查询替代产品推荐给客户
3. 如客户同意替代品，使用替代产品创建订单
