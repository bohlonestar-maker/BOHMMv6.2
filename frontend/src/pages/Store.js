import { useState, useEffect, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { PaymentForm, CreditCard } from "react-square-web-payments-sdk";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "../components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { Textarea } from "../components/ui/textarea";
import {
  ShoppingCart,
  Plus,
  Minus,
  Trash2,
  Package,
  CreditCard as CreditCardIcon,
  DollarSign,
  ArrowLeft,
  CheckCircle,
  Clock,
  Truck,
  XCircle,
  RefreshCw,
  Edit,
  Image as ImageIcon,
} from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;
const SQUARE_APP_ID = process.env.REACT_APP_SQUARE_APPLICATION_ID;
const SQUARE_LOCATION_ID = process.env.REACT_APP_SQUARE_LOCATION_ID;

export default function Store({ userRole, userChapter }) {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState("merchandise");
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState({ items: [], total: 0, item_count: 0 });
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [cartOpen, setCartOpen] = useState(false);
  const [checkoutOpen, setCheckoutOpen] = useState(false);
  const [addProductOpen, setAddProductOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [processingPayment, setProcessingPayment] = useState(false);
  const [currentOrder, setCurrentOrder] = useState(null);
  const [shippingAddress, setShippingAddress] = useState("");
  const [orderNotes, setOrderNotes] = useState("");
  const [canManageStore, setCanManageStore] = useState(false);
  const [redirectingToCheckout, setRedirectingToCheckout] = useState(false);
  
  // Dues state
  const [duesYear, setDuesYear] = useState(new Date().getFullYear());
  const [duesMonth, setDuesMonth] = useState(new Date().getMonth()); // 0-indexed month
  const [duesCheckoutOpen, setDuesCheckoutOpen] = useState(false);
  const [duesOrder, setDuesOrder] = useState(null);
  const MONTHLY_DUES_AMOUNT = 30.00; // Fixed monthly dues amount

  // Month names for display
  const monthNames = ["January", "February", "March", "April", "May", "June", 
                      "July", "August", "September", "October", "November", "December"];

  // Product form state
  const [productForm, setProductForm] = useState({
    name: "",
    description: "",
    price: "",
    category: "merchandise",
    image_url: "",
    inventory_count: 0,
    member_price: "",
    show_in_supporter_store: true, // Default to showing in supporter store
    allows_customization: false, // Default to no customization
  });

  const isAdmin = userRole === "admin";

  const fetchProducts = useCallback(async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API_URL}/api/store/products`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setProducts(response.data);
      // Check if any product has can_manage flag (indicates user permission)
      if (response.data.length > 0 && response.data[0].can_manage !== undefined) {
        setCanManageStore(response.data[0].can_manage);
      }
    } catch (error) {
      console.error("Error fetching products:", error);
      toast.error("Failed to load products");
    }
  }, []);

  const fetchCart = useCallback(async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API_URL}/api/store/cart`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setCart(response.data);
    } catch (error) {
      console.error("Error fetching cart:", error);
    }
  }, []);

  const fetchOrders = useCallback(async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API_URL}/api/store/orders`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setOrders(response.data);
    } catch (error) {
      console.error("Error fetching orders:", error);
    }
  }, []);

  // Handle return from Square hosted checkout
  useEffect(() => {
    const paymentStatus = searchParams.get("payment");
    const orderId = searchParams.get("order_id");
    
    if (paymentStatus === "success" && orderId) {
      // Payment completed - show success message and switch to orders tab
      toast.success("Payment successful! Your order has been placed.");
      setActiveTab("orders");
      // Clear the URL params
      setSearchParams({});
      // Refresh orders to show the new order
      fetchOrders();
    }
  }, [searchParams, setSearchParams, fetchOrders]);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchProducts(), fetchCart(), fetchOrders()]);
      setLoading(false);
    };
    loadData();
  }, [fetchProducts, fetchCart, fetchOrders]);

  // Product selection state for size/customization modal
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [productModalOpen, setProductModalOpen] = useState(false);
  const [selectedVariation, setSelectedVariation] = useState(null);
  const [addHandle, setAddHandle] = useState(false);
  const [handleText, setHandleText] = useState("");
  const [addRank, setAddRank] = useState(false);
  const [rankText, setRankText] = useState("");

  // Customization prices
  const HANDLE_PRICE = 5.00;
  const RANK_PRICE = 5.00;

  const openProductModal = (product) => {
    setSelectedProduct(product);
    setSelectedVariation(null);
    setAddHandle(false);
    setHandleText("");
    setAddRank(false);
    setRankText("");
    setProductModalOpen(true);
  };

  // Calculate total price including customizations
  const calculateTotalPrice = () => {
    if (!selectedProduct) return 0;
    let price = selectedVariation?.price || selectedProduct.display_price || selectedProduct.price;
    if (addHandle) price += HANDLE_PRICE;
    if (addRank) price += RANK_PRICE;
    return price;
  };

  const addToCart = async (product, variationId = null, customization = null) => {
    try {
      const token = localStorage.getItem("token");
      let url = `${API_URL}/api/store/cart/add?product_id=${product.id}&quantity=1`;
      if (variationId) {
        url += `&variation_id=${variationId}`;
      }
      if (customization) {
        url += `&customization=${encodeURIComponent(customization)}`;
      }
      
      // Include add-on prices in the request
      let addOnPrice = 0;
      if (addHandle) addOnPrice += HANDLE_PRICE;
      if (addRank) addOnPrice += RANK_PRICE;
      if (addOnPrice > 0) {
        url += `&add_on_price=${addOnPrice}`;
      }
      
      await axios.post(url, {}, { headers: { Authorization: `Bearer ${token}` } });
      await fetchCart();
      toast.success("Added to cart!");
      setProductModalOpen(false);
      setSelectedProduct(null);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to add to cart");
    }
  };

  const handleAddToCartClick = (product) => {
    // If product has variations or allows customization, open modal
    if (product.has_variations || product.allows_customization) {
      openProductModal(product);
    } else {
      // Add directly to cart
      addToCart(product);
    }
  };

  const handleConfirmAddToCart = () => {
    if (!selectedProduct) return;
    
    if (selectedProduct.has_variations && !selectedVariation) {
      toast.error("Please select a size");
      return;
    }
    
    // Validate customization inputs
    if (addHandle && !handleText.trim()) {
      toast.error("Please enter your handle or uncheck 'Add your Handle'");
      return;
    }
    if (addRank && !rankText.trim()) {
      toast.error("Please enter your rank or uncheck 'Add your Rank'");
      return;
    }
    
    // Build customization string
    let customization = null;
    const parts = [];
    if (addHandle && handleText.trim()) {
      parts.push(`Handle: ${handleText.trim()}`);
    }
    if (addRank && rankText.trim()) {
      parts.push(`Rank: ${rankText.trim()}`);
    }
    if (parts.length > 0) {
      customization = parts.join(' | ');
    }
    
    addToCart(selectedProduct, selectedVariation?.id, customization);
  };

  const updateCartItem = async (item, quantity) => {
    try {
      const token = localStorage.getItem("token");
      let url = `${API_URL}/api/store/cart/update?product_id=${item.product_id}&quantity=${quantity}`;
      if (item.variation_id) {
        url += `&variation_id=${item.variation_id}`;
      }
      if (item.customization) {
        url += `&customization=${encodeURIComponent(item.customization)}`;
      }
      await axios.put(url, {}, { headers: { Authorization: `Bearer ${token}` } });
      await fetchCart();
    } catch (error) {
      toast.error("Failed to update cart");
    }
  };

  const clearCart = async () => {
    try {
      const token = localStorage.getItem("token");
      await axios.delete(`${API_URL}/api/store/cart/clear`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      await fetchCart();
      toast.success("Cart cleared");
    } catch (error) {
      toast.error("Failed to clear cart");
    }
  };

  const createOrder = async () => {
    try {
      setRedirectingToCheckout(true);
      const token = localStorage.getItem("token");
      const response = await axios.post(
        `${API_URL}/api/store/checkout`,
        null,
        {
          params: { shipping_address: shippingAddress, notes: orderNotes },
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      
      if (response.data.success && response.data.checkout_url) {
        // Close the cart dialog
        setCartOpen(false);
        // Redirect to Square's hosted checkout page
        window.location.href = response.data.checkout_url;
      } else {
        toast.error("Failed to create checkout link");
        setRedirectingToCheckout(false);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to create checkout");
      setRedirectingToCheckout(false);
    }
  };

  // Dues payment handlers
  const createDuesOrder = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.post(
        `${API_URL}/api/store/dues/pay`,
        null,
        {
          params: { amount: MONTHLY_DUES_AMOUNT, year: duesYear, month: duesMonth },
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      setDuesOrder(response.data);
      setDuesCheckoutOpen(true);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to create dues order");
    }
  };

  const handleDuesPaymentComplete = async (token) => {
    if (!duesOrder) return;
    
    setProcessingPayment(true);
    try {
      const authToken = localStorage.getItem("token");
      const response = await axios.post(
        `${API_URL}/api/store/orders/${duesOrder.order_id}/pay`,
        {
          source_id: token.token,
          amount_cents: duesOrder.total_cents,
          order_id: duesOrder.order_id,
        },
        { headers: { Authorization: `Bearer ${authToken}` } }
      );

      if (response.data.success) {
        toast.success("Dues payment successful! Your member record has been updated.");
        setDuesCheckoutOpen(false);
        setDuesOrder(null);
        await fetchOrders();
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Dues payment failed");
    } finally {
      setProcessingPayment(false);
    }
  };

  // Product management (admin)
  const handleCreateProduct = async () => {
    try {
      const token = localStorage.getItem("token");
      const data = {
        ...productForm,
        price: parseFloat(productForm.price),
        member_price: productForm.member_price ? parseFloat(productForm.member_price) : null,
        inventory_count: parseInt(productForm.inventory_count),
        show_in_supporter_store: productForm.show_in_supporter_store,
      };
      
      if (editingProduct) {
        await axios.put(
          `${API_URL}/api/store/products/${editingProduct.id}`,
          data,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        toast.success("Product updated!");
      } else {
        await axios.post(`${API_URL}/api/store/products`, data, {
          headers: { Authorization: `Bearer ${token}` },
        });
        toast.success("Product created!");
      }
      
      setAddProductOpen(false);
      setEditingProduct(null);
      setProductForm({
        name: "",
        description: "",
        price: "",
        category: "merchandise",
        image_url: "",
        inventory_count: 0,
        member_price: "",
        show_in_supporter_store: true,
      });
      await fetchProducts();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to save product");
    }
  };

  const handleEditProduct = (product) => {
    setEditingProduct(product);
    setProductForm({
      name: product.name,
      description: product.description || "",
      price: product.price.toString(),
      category: product.category,
      image_url: product.image_url || "",
      inventory_count: product.inventory_count,
      member_price: product.member_price?.toString() || "",
      show_in_supporter_store: product.show_in_supporter_store !== false, // Default true if not set
      allows_customization: product.allows_customization || false,
    });
    setAddProductOpen(true);
  };

  const handleDeleteProduct = async (productId) => {
    if (!window.confirm("Are you sure you want to delete this product?")) return;
    
    try {
      const token = localStorage.getItem("token");
      await axios.delete(`${API_URL}/api/store/products/${productId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success("Product deleted");
      await fetchProducts();
    } catch (error) {
      toast.error("Failed to delete product");
    }
  };

  const updateOrderStatus = async (orderId, status) => {
    try {
      const token = localStorage.getItem("token");
      await axios.put(
        `${API_URL}/api/store/orders/${orderId}/status?status=${status}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success("Order status updated");
      await fetchOrders();
    } catch (error) {
      toast.error("Failed to update order status");
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      pending: { color: "bg-yellow-500", icon: Clock },
      paid: { color: "bg-green-500", icon: CheckCircle },
      shipped: { color: "bg-blue-500", icon: Truck },
      completed: { color: "bg-emerald-600", icon: CheckCircle },
      cancelled: { color: "bg-red-500", icon: XCircle },
      refunded: { color: "bg-purple-500", icon: RefreshCw },
    };
    const config = statusConfig[status] || statusConfig.pending;
    const Icon = config.icon;
    
    return (
      <Badge className={`${config.color} text-white flex items-center gap-1`}>
        <Icon className="w-3 h-3" />
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  const merchandiseProducts = products.filter(p => p.category === "merchandise");
  const duesProducts = products.filter(p => p.category === "dues");

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-white">Loading store...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 p-2 sm:p-4 md:p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto">
        {/* Mobile-optimized header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4 sm:mb-6">
          <div className="flex items-center justify-between sm:justify-start gap-2 sm:gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate("/")}
              className="text-slate-300 hover:text-white px-2 sm:px-3"
            >
              <ArrowLeft className="w-4 h-4 sm:mr-2" />
              <span className="hidden sm:inline">Back</span>
            </Button>
            <h1 className="text-lg sm:text-2xl font-bold text-white flex items-center gap-2">
              <Package className="w-5 h-5 sm:w-6 sm:h-6" />
              BOHTC Store
            </h1>
          </div>
          
          <div className="flex items-center justify-end gap-2 sm:gap-3">
            {canManageStore && (
              <Button
                size="sm"
                onClick={() => {
                  setEditingProduct(null);
                  setProductForm({
                    name: "",
                    description: "",
                    price: "",
                    category: "merchandise",
                    image_url: "",
                    inventory_count: 0,
                    member_price: "",
                    show_in_supporter_store: true,
                  });
                  setAddProductOpen(true);
                }}
                className="bg-green-600 hover:bg-green-700 text-xs sm:text-sm"
              >
                <Plus className="w-4 h-4 sm:mr-2" />
                <span className="hidden sm:inline">Add Product</span>
              </Button>
            )}
            <Button
              onClick={() => setCartOpen(true)}
              variant="outline"
              size="sm"
              className="relative border-slate-600 text-slate-200 hover:bg-slate-700"
            >
              <ShoppingCart className="w-4 h-4 sm:mr-2" />
              <span className="hidden sm:inline">Cart</span>
              {cart.item_count > 0 && (
                <Badge className="absolute -top-2 -right-2 bg-red-500 text-white text-xs px-1.5 min-w-[20px] h-5 flex items-center justify-center">
                  {cart.item_count}
                </Badge>
              )}
            </Button>
          </div>
        </div>

        {/* Main Content Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="bg-slate-800 border-slate-700 mb-4 sm:mb-6 w-full sm:w-auto grid grid-cols-3 sm:flex">
            <TabsTrigger value="merchandise" className="data-[state=active]:bg-slate-700 text-xs sm:text-sm px-2 sm:px-4">
              <Package className="w-3 h-3 sm:w-4 sm:h-4 sm:mr-2" />
              <span className="hidden sm:inline">Merchandise</span>
              <span className="sm:hidden">Shop</span>
            </TabsTrigger>
            <TabsTrigger value="dues" className="data-[state=active]:bg-slate-700 text-xs sm:text-sm px-2 sm:px-4">
              <DollarSign className="w-3 h-3 sm:w-4 sm:h-4 sm:mr-2" />
              <span className="hidden sm:inline">Pay Dues</span>
              <span className="sm:hidden">Dues</span>
            </TabsTrigger>
            <TabsTrigger value="orders" className="data-[state=active]:bg-slate-700 text-xs sm:text-sm px-2 sm:px-4">
              <CreditCardIcon className="w-3 h-3 sm:w-4 sm:h-4 sm:mr-2" />
              <span className="hidden sm:inline">My Orders</span>
              <span className="sm:hidden">Orders</span>
            </TabsTrigger>
          </TabsList>

          {/* Merchandise Tab */}
          <TabsContent value="merchandise">
            {merchandiseProducts.length === 0 ? (
              <div className="text-center py-8 sm:py-12 text-slate-400">
                <Package className="w-10 h-10 sm:w-12 sm:h-12 mx-auto mb-4 opacity-50" />
                <p className="text-sm sm:text-base">No merchandise available yet.</p>
                {canManageStore && <p className="text-xs sm:text-sm mt-2">Click &quot;Add Product&quot; to add items.</p>}
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 sm:gap-4">
                {merchandiseProducts.map((product) => (
                  <Card key={product.id} className="bg-slate-800 border-slate-700 flex flex-col">
                    <CardHeader className="p-2 sm:p-4 pb-2">
                      {product.image_url ? (
                        <img
                          src={product.image_url}
                          alt={product.name}
                          className="w-full h-32 sm:h-40 md:h-48 object-cover rounded-md mb-2"
                        />
                      ) : (
                        <div className="w-full h-32 sm:h-40 md:h-48 bg-slate-700 rounded-md flex items-center justify-center mb-2">
                          <ImageIcon className="w-8 h-8 sm:w-12 sm:h-12 text-slate-500" />
                        </div>
                      )}
                      <CardTitle className="text-white text-sm sm:text-base md:text-lg line-clamp-2">{product.name}</CardTitle>
                      {product.description && (
                        <CardDescription className="text-slate-400 text-xs sm:text-sm line-clamp-2 hidden sm:block">
                          {product.description}
                        </CardDescription>
                      )}
                    </CardHeader>
                    <CardContent className="p-2 sm:p-4 pt-0 flex-1">
                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-2">
                        <div>
                          {product.is_member_price ? (
                            <div className="flex flex-wrap items-center gap-1 sm:gap-2">
                              <span className="text-base sm:text-xl font-bold text-green-400">
                                ${product.display_price.toFixed(2)}
                              </span>
                              <span className="text-xs sm:text-sm text-slate-500 line-through">
                                ${product.price.toFixed(2)}
                              </span>
                              <Badge className="bg-green-600 text-[10px] sm:text-xs">Member</Badge>
                            </div>
                          ) : (
                            <span className="text-base sm:text-xl font-bold text-white">
                              {product.has_variations ? `From $${product.display_price.toFixed(2)}` : `$${product.display_price.toFixed(2)}`}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="text-xs sm:text-sm text-slate-400 mb-2">
                        {product.inventory_count > 0 ? (
                          <span className="text-green-400">{product.inventory_count} in stock</span>
                        ) : (
                          <span className="text-red-400">Out of stock</span>
                        )}
                      </div>
                      {/* Show size/variation badges - hidden on mobile, visible on larger screens */}
                      {product.has_variations && product.variations && (
                        <div className="hidden sm:flex flex-wrap gap-1 mb-2">
                          {product.variations.slice(0, 6).map((v) => (
                            <Badge 
                              key={v.id} 
                              variant="outline" 
                              className={`text-[10px] sm:text-xs ${v.sold_out || v.inventory_count === 0 ? 'text-slate-500 border-slate-600 line-through' : 'text-slate-300 border-slate-500'}`}
                            >
                              {v.name}
                            </Badge>
                          ))}
                          {product.variations.length > 6 && (
                            <Badge variant="outline" className="text-[10px] sm:text-xs text-slate-400">
                              +{product.variations.length - 6}
                            </Badge>
                          )}
                        </div>
                      )}
                      {product.allows_customization && (
                        <Badge className="bg-purple-600 text-[10px] sm:text-xs">Add Handle</Badge>
                      )}
                    </CardContent>
                    <CardFooter className="p-2 sm:p-4 pt-0 flex flex-col sm:flex-row gap-2">
                      <Button
                        onClick={() => handleAddToCartClick(product)}
                        disabled={product.inventory_count === 0}
                        className="w-full sm:flex-1 bg-blue-600 hover:bg-blue-700 text-xs sm:text-sm py-2"
                        size="sm"
                      >
                        <ShoppingCart className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2" />
                        {product.has_variations ? 'Options' : 'Add'}
                      </Button>
                      {canManageStore && (
                        <div className="flex gap-2 w-full sm:w-auto">
                          <Button
                            size="icon"
                            variant="outline"
                            onClick={() => handleEditProduct(product)}
                            className="border-slate-600 flex-1 sm:flex-none h-8 w-8 sm:h-9 sm:w-9"
                          >
                            <Edit className="w-3 h-3 sm:w-4 sm:h-4" />
                          </Button>
                          <Button
                            size="icon"
                            variant="outline"
                            onClick={() => handleDeleteProduct(product.id)}
                            className="border-red-600 text-red-400 hover:bg-red-900 flex-1 sm:flex-none h-8 w-8 sm:h-9 sm:w-9"
                          >
                            <Trash2 className="w-3 h-3 sm:w-4 sm:h-4" />
                          </Button>
                        </div>
                      )}
                    </CardFooter>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Dues Tab */}
          <TabsContent value="dues">
            <Card className="bg-slate-800 border-slate-700 max-w-md mx-auto">
              <CardHeader className="p-3 sm:p-4">
                <CardTitle className="text-white flex items-center gap-2 text-base sm:text-lg">
                  <DollarSign className="w-4 h-4 sm:w-5 sm:h-5" />
                  Pay Monthly Dues
                </CardTitle>
                <CardDescription className="text-slate-400 text-xs sm:text-sm">
                  Pay your monthly membership dues ($30.00/month)
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 sm:space-y-4 p-3 sm:p-4 pt-0">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-slate-200 text-xs sm:text-sm">Year</Label>
                    <Select value={duesYear.toString()} onValueChange={(v) => setDuesYear(parseInt(v))}>
                      <SelectTrigger className="bg-slate-700 border-slate-600 text-white text-sm">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-slate-700">
                        {[2024, 2025, 2026].map((year) => (
                          <SelectItem key={year} value={year.toString()} className="text-white">
                            {year}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-slate-200 text-xs sm:text-sm">Month</Label>
                    <Select value={duesMonth.toString()} onValueChange={(v) => setDuesMonth(parseInt(v))}>
                      <SelectTrigger className="bg-slate-700 border-slate-600 text-white text-sm">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-slate-700">
                        {monthNames.map((month, idx) => (
                          <SelectItem key={idx} value={idx.toString()} className="text-white">
                            {month}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="bg-slate-700/50 rounded-lg p-3 text-center">
                  <div className="text-slate-400 text-xs sm:text-sm">Amount Due</div>
                  <div className="text-2xl sm:text-3xl font-bold text-green-400">
                    ${MONTHLY_DUES_AMOUNT.toFixed(2)}
                  </div>
                  <div className="text-slate-500 text-xs mt-1">
                    for {monthNames[duesMonth]} {duesYear}
                  </div>
                </div>
              </CardContent>
              <CardFooter className="p-3 sm:p-4 pt-0">
                <Button
                  onClick={createDuesOrder}
                  className="w-full bg-green-600 hover:bg-green-700 text-sm"
                >
                  <CreditCardIcon className="w-4 h-4 mr-2" />
                  Pay ${MONTHLY_DUES_AMOUNT.toFixed(2)} for {monthNames[duesMonth]}
                </Button>
              </CardFooter>
            </Card>
          </TabsContent>

          {/* Orders Tab */}
          <TabsContent value="orders">
            {orders.length === 0 ? (
              <div className="text-center py-8 sm:py-12 text-slate-400">
                <CreditCardIcon className="w-10 h-10 sm:w-12 sm:h-12 mx-auto mb-4 opacity-50" />
                <p className="text-sm sm:text-base">No orders yet.</p>
              </div>
            ) : (
              <div className="space-y-3 sm:space-y-4">
                {orders.map((order) => (
                  <Card key={order.id} className="bg-slate-800 border-slate-700">
                    <CardHeader className="p-3 sm:p-4 pb-2">
                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                        <div>
                          <CardTitle className="text-white text-sm sm:text-lg">
                            Order #{order.id.slice(0, 8)}
                          </CardTitle>
                          <CardDescription className="text-slate-400 text-xs sm:text-sm">
                            {new Date(order.created_at).toLocaleDateString()} at{" "}
                            {new Date(order.created_at).toLocaleTimeString()}
                          </CardDescription>
                        </div>
                        <div className="flex items-center gap-2 flex-wrap">
                          {getStatusBadge(order.status)}
                          {canManageStore && order.status === "paid" && (
                            <Select
                              value={order.status}
                              onValueChange={(v) => updateOrderStatus(order.id, v)}
                            >
                              <SelectTrigger className="w-24 sm:w-32 bg-slate-700 border-slate-600 text-white text-xs">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent className="bg-slate-800 border-slate-700">
                                <SelectItem value="shipped" className="text-white">Ship</SelectItem>
                                <SelectItem value="completed" className="text-white">Complete</SelectItem>
                                <SelectItem value="cancelled" className="text-white">Cancel</SelectItem>
                              </SelectContent>
                            </Select>
                          )}
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="p-3 sm:p-4 pt-0">
                      {/* Mobile-friendly order items */}
                      <div className="space-y-2 sm:hidden">
                        {order.items.map((item, idx) => (
                          <div key={idx} className="bg-slate-700/50 rounded p-2 text-xs">
                            <div className="text-white font-medium">{item.name}</div>
                            <div className="flex justify-between text-slate-400 mt-1">
                              <span>Qty: {item.quantity}</span>
                              <span>${(item.price * item.quantity).toFixed(2)}</span>
                            </div>
                          </div>
                        ))}
                        <div className="flex justify-between pt-2 border-t border-slate-700 text-sm font-bold text-white">
                          <span>Total:</span>
                          <span>${order.total.toFixed(2)}</span>
                        </div>
                      </div>
                      {/* Desktop table view */}
                      <div className="hidden sm:block">
                        <Table>
                          <TableHeader>
                            <TableRow className="border-slate-700">
                              <TableHead className="text-slate-400">Item</TableHead>
                              <TableHead className="text-slate-400 text-right">Qty</TableHead>
                            <TableHead className="text-slate-400 text-right">Price</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {order.items.map((item, idx) => (
                            <TableRow key={idx} className="border-slate-700">
                              <TableCell className="text-white">{item.name}</TableCell>
                              <TableCell className="text-white text-right">{item.quantity}</TableCell>
                              <TableCell className="text-white text-right">
                                ${(item.price * item.quantity).toFixed(2)}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                      <div className="mt-4 pt-4 border-t border-slate-700 space-y-1 text-right">
                        <div className="text-slate-400 text-sm">Subtotal: ${order.subtotal.toFixed(2)}</div>
                        {order.tax > 0 && (
                          <div className="text-slate-400 text-sm">Tax: ${order.tax.toFixed(2)}</div>
                        )}
                        <div className="text-lg sm:text-xl font-bold text-white">
                          Total: ${order.total.toFixed(2)}
                        </div>
                      </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>

      {/* Cart Dialog */}
      <Dialog open={cartOpen} onOpenChange={setCartOpen}>
        <DialogContent className="bg-slate-800 border-slate-700 max-w-[95vw] sm:max-w-lg mx-2 sm:mx-auto">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2 text-base sm:text-lg">
              <ShoppingCart className="w-4 h-4 sm:w-5 sm:h-5" />
              Shopping Cart
            </DialogTitle>
          </DialogHeader>
          {cart.items.length === 0 ? (
            <div className="text-center py-6 sm:py-8 text-slate-400 text-sm sm:text-base">
              Your cart is empty
            </div>
          ) : (
            <>
              <div className="space-y-2 sm:space-y-3 max-h-48 sm:max-h-64 overflow-y-auto">
                {cart.items.map((item, idx) => (
                  <div
                    key={`${item.product_id}-${item.variation_id || ''}-${item.customization || ''}-${idx}`}
                    className="flex flex-col sm:flex-row sm:items-center justify-between p-2 sm:p-3 bg-slate-700 rounded-lg gap-2"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="text-white font-medium text-sm sm:text-base truncate">{item.name}</div>
                      <div className="text-slate-400 text-xs sm:text-sm">
                        ${item.price.toFixed(2)} each
                      </div>
                    </div>
                    <div className="flex items-center gap-1 sm:gap-2 justify-end">
                      <Button
                        size="icon"
                        variant="outline"
                        onClick={() => updateCartItem(item, item.quantity - 1)}
                        className="h-7 w-7 sm:h-8 sm:w-8 border-slate-600"
                      >
                        <Minus className="w-3 h-3" />
                      </Button>
                      <span className="text-white w-6 sm:w-8 text-center text-sm">{item.quantity}</span>
                      <Button
                        size="icon"
                        variant="outline"
                        onClick={() => updateCartItem(item, item.quantity + 1)}
                        className="h-7 w-7 sm:h-8 sm:w-8 border-slate-600"
                      >
                        <Plus className="w-3 h-3" />
                      </Button>
                      <Button
                        size="icon"
                        variant="ghost"
                        onClick={() => updateCartItem(item, 0)}
                        className="h-7 w-7 sm:h-8 sm:w-8 text-red-400 hover:text-red-300"
                      >
                        <Trash2 className="w-3 h-3 sm:w-4 sm:h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
              <div className="border-t border-slate-700 pt-3 sm:pt-4 space-y-2 sm:space-y-3">
                <div className="flex justify-between text-lg sm:text-xl font-bold text-white">
                  <span>Total:</span>
                  <span>${cart.total.toFixed(2)}</span>
                </div>
                <div>
                  <Label className="text-slate-200 text-xs sm:text-sm">Shipping Address (optional)</Label>
                  <Textarea
                    value={shippingAddress}
                    onChange={(e) => setShippingAddress(e.target.value)}
                    placeholder="Enter shipping address..."
                    className="bg-slate-700 border-slate-600 text-white mt-1 text-sm"
                    rows={2}
                  />
                </div>
                <div>
                  <Label className="text-slate-200 text-xs sm:text-sm">Order Notes (optional)</Label>
                  <Input
                    value={orderNotes}
                    onChange={(e) => setOrderNotes(e.target.value)}
                    placeholder="Any special instructions..."
                    className="bg-slate-700 border-slate-600 text-white mt-1 text-sm"
                  />
                </div>
              </div>
            </>
          )}
          <DialogFooter className="flex flex-col sm:flex-row gap-2">
            <Button variant="outline" onClick={clearCart} className="border-slate-600 text-sm w-full sm:w-auto" disabled={redirectingToCheckout}>
              Clear Cart
            </Button>
            <Button
              onClick={createOrder}
              disabled={cart.items.length === 0 || redirectingToCheckout}
              className="bg-green-600 hover:bg-green-700 text-sm w-full sm:w-auto"
            >
              {redirectingToCheckout ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Redirecting...
                </>
              ) : (
                "Proceed to Checkout"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dues Checkout Dialog */}
      <Dialog open={duesCheckoutOpen} onOpenChange={setDuesCheckoutOpen}>
        <DialogContent className="bg-slate-800 border-slate-700 max-w-[95vw] sm:max-w-md mx-2 sm:mx-auto">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2 text-sm sm:text-base">
              <DollarSign className="w-4 h-4 sm:w-5 sm:h-5" />
              Pay Monthly Dues
            </DialogTitle>
            <DialogDescription className="text-slate-400 text-xs sm:text-sm">
              {monthNames[duesMonth]} {duesYear} - ${duesOrder?.total.toFixed(2)}
            </DialogDescription>
          </DialogHeader>
          <div className="py-3 sm:py-4">
            <PaymentForm
              applicationId={SQUARE_APP_ID}
              locationId={SQUARE_LOCATION_ID}
              cardTokenizeResponseReceived={handleDuesPaymentComplete}
              createPaymentRequest={() => ({
                countryCode: "US",
                currencyCode: "USD",
                total: {
                  amount: duesOrder?.total.toString() || "0",
                  label: "Monthly Dues",
                },
              })}
            >
              <CreditCard />
              <Button
                type="submit"
                disabled={processingPayment}
                className="w-full mt-4 bg-green-600 hover:bg-green-700 text-sm"
              >
                {processingPayment ? "Processing..." : `Pay $${duesOrder?.total.toFixed(2)}`}
              </Button>
            </PaymentForm>
          </div>
          <div className="text-xs text-slate-500 text-center">
            🔒 Payments processed securely by Square
          </div>
        </DialogContent>
      </Dialog>

      {/* Add/Edit Product Dialog */}
      <Dialog open={addProductOpen} onOpenChange={setAddProductOpen}>
        <DialogContent className="bg-slate-800 border-slate-700 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white">
              {editingProduct ? "Edit Product" : "Add New Product"}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label className="text-slate-200">Name</Label>
              <Input
                value={productForm.name}
                onChange={(e) => setProductForm({ ...productForm, name: e.target.value })}
                className="bg-slate-700 border-slate-600 text-white"
                placeholder="Product name"
              />
            </div>
            <div>
              <Label className="text-slate-200">Description</Label>
              <Textarea
                value={productForm.description}
                onChange={(e) => setProductForm({ ...productForm, description: e.target.value })}
                className="bg-slate-700 border-slate-600 text-white"
                placeholder="Product description"
                rows={2}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-200">Price ($)</Label>
                <Input
                  type="number"
                  value={productForm.price}
                  onChange={(e) => setProductForm({ ...productForm, price: e.target.value })}
                  className="bg-slate-700 border-slate-600 text-white"
                  placeholder="0.00"
                  step="0.01"
                />
              </div>
              <div>
                <Label className="text-slate-200">Member Price ($)</Label>
                <Input
                  type="number"
                  value={productForm.member_price}
                  onChange={(e) => setProductForm({ ...productForm, member_price: e.target.value })}
                  className="bg-slate-700 border-slate-600 text-white"
                  placeholder="Optional"
                  step="0.01"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-200">Category</Label>
                <Select
                  value={productForm.category}
                  onValueChange={(v) => setProductForm({ ...productForm, category: v })}
                >
                  <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-700">
                    <SelectItem value="merchandise" className="text-white">Merchandise</SelectItem>
                    <SelectItem value="dues" className="text-white">Dues</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-slate-200">Inventory</Label>
                <Input
                  type="number"
                  value={productForm.inventory_count}
                  onChange={(e) => setProductForm({ ...productForm, inventory_count: parseInt(e.target.value) || 0 })}
                  className="bg-slate-700 border-slate-600 text-white"
                  min="0"
                />
              </div>
            </div>
            <div>
              <Label className="text-slate-200">Image URL</Label>
              <Input
                value={productForm.image_url}
                onChange={(e) => setProductForm({ ...productForm, image_url: e.target.value })}
                className="bg-slate-700 border-slate-600 text-white"
                placeholder="https://example.com/image.jpg"
              />
            </div>
            {/* Supporter Store Toggle */}
            <div className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg border border-slate-600">
              <div>
                <Label className="text-slate-200 font-medium">Show in Supporter Store</Label>
                <p className="text-xs text-slate-400 mt-1">
                  Allow non-members to purchase this item
                </p>
              </div>
              <button
                type="button"
                onClick={() => setProductForm({ ...productForm, show_in_supporter_store: !productForm.show_in_supporter_store })}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  productForm.show_in_supporter_store ? 'bg-green-600' : 'bg-slate-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    productForm.show_in_supporter_store ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddProductOpen(false)} className="border-slate-600">
              Cancel
            </Button>
            <Button onClick={handleCreateProduct} className="bg-green-600 hover:bg-green-700">
              {editingProduct ? "Update" : "Create"} Product
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Product Options Modal (Size/Customization) */}
      <Dialog open={productModalOpen} onOpenChange={setProductModalOpen}>
        <DialogContent className="bg-slate-800 border-slate-700 max-w-[95vw] sm:max-w-md mx-2 sm:mx-auto max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2 text-sm sm:text-base">
              <Package className="w-4 h-4 sm:w-5 sm:h-5" />
              <span className="line-clamp-1">{selectedProduct?.name}</span>
            </DialogTitle>
            {selectedProduct?.description && (
              <DialogDescription className="text-slate-400 text-xs sm:text-sm line-clamp-2">
                {selectedProduct.description}
              </DialogDescription>
            )}
          </DialogHeader>
          
          {selectedProduct && (
            <div className="space-y-3 sm:space-y-4">
              {/* Product Image */}
              {selectedProduct.image_url && (
                <img
                  src={selectedProduct.image_url}
                  alt={selectedProduct.name}
                  className="w-full h-32 sm:h-48 object-cover rounded-md"
                />
              )}
              
              {/* Size Selection */}
              {selectedProduct.has_variations && selectedProduct.variations && (
                <div>
                  <Label className="text-slate-200 mb-2 block text-xs sm:text-sm">Select Size *</Label>
                  <div className="grid grid-cols-4 sm:grid-cols-5 gap-1 sm:gap-2">
                    {selectedProduct.variations.map((variation) => (
                      <Button
                        key={variation.id}
                        variant={selectedVariation?.id === variation.id ? "default" : "outline"}
                        disabled={variation.sold_out || variation.inventory_count === 0}
                        onClick={() => setSelectedVariation(variation)}
                        size="sm"
                        className={`
                          text-xs sm:text-sm px-2 py-1 sm:px-3 sm:py-2
                          ${selectedVariation?.id === variation.id 
                            ? 'bg-blue-600 text-white' 
                            : 'border-slate-600 text-slate-300 hover:bg-slate-700'}
                          ${(variation.sold_out || variation.inventory_count === 0) && 'opacity-50 line-through'}
                        `}
                      >
                        {variation.name}
                      </Button>
                    ))}
                  </div>
                  {selectedVariation && (
                    <div className="mt-2 text-xs sm:text-sm text-slate-400">
                      Price: <span className="text-green-400 font-bold">${selectedVariation.price.toFixed(2)}</span>
                      {selectedVariation.inventory_count > 0 && (
                        <span className="ml-2">({selectedVariation.inventory_count} in stock)</span>
                      )}
                    </div>
                  )}
                </div>
              )}
              
              {/* Add Text Options (Handle and Rank) */}
              {selectedProduct.allows_customization && (
                <div className="space-y-2 sm:space-y-3 border border-slate-600 rounded-lg p-2 sm:p-4 bg-slate-700/30">
                  <Label className="text-slate-200 font-semibold block text-xs sm:text-sm">Add Text</Label>
                  
                  {/* Add Handle Checkbox */}
                  <div className="space-y-1 sm:space-y-2">
                    <div className="flex items-center gap-2 sm:gap-3">
                      <input
                        type="checkbox"
                        id="addHandle"
                        checked={addHandle}
                        onChange={(e) => {
                          setAddHandle(e.target.checked);
                          if (!e.target.checked) setHandleText("");
                        }}
                        className="w-4 h-4 rounded border-slate-500 bg-slate-700 text-blue-600 focus:ring-blue-500"
                      />
                      <label htmlFor="addHandle" className="text-slate-300 flex-1 text-xs sm:text-sm">
                        Add your Handle
                      </label>
                      <span className="text-green-400 font-semibold text-xs sm:text-sm">+$5.00</span>
                    </div>
                    {addHandle && (
                      <Input
                        value={handleText}
                        onChange={(e) => setHandleText(e.target.value)}
                        placeholder="Enter your handle"
                        className="bg-slate-700 border-slate-600 text-white text-sm"
                        maxLength={30}
                      />
                    )}
                  </div>
                  
                  {/* Add Rank Checkbox */}
                  <div className="space-y-1 sm:space-y-2">
                    <div className="flex items-center gap-2 sm:gap-3">
                      <input
                        type="checkbox"
                        id="addRank"
                        checked={addRank}
                        onChange={(e) => {
                          setAddRank(e.target.checked);
                          if (!e.target.checked) setRankText("");
                        }}
                        className="w-4 h-4 rounded border-slate-500 bg-slate-700 text-blue-600 focus:ring-blue-500"
                      />
                      <label htmlFor="addRank" className="text-slate-300 flex-1 text-xs sm:text-sm">
                        Add your Rank <span className="text-slate-500 text-[10px] sm:text-xs">(Officer&apos;s Only)</span>
                      </label>
                      <span className="text-green-400 font-semibold text-xs sm:text-sm">+$5.00</span>
                    </div>
                    {addRank && (
                      <Input
                        value={rankText}
                        onChange={(e) => setRankText(e.target.value)}
                        placeholder="Enter your rank"
                        className="bg-slate-700 border-slate-600 text-white text-sm"
                        maxLength={30}
                      />
                    )}
                  </div>
                  
                  <p className="text-[10px] sm:text-xs text-amber-400 mt-2">
                    ⚠️ If you add your rank or handle without checking the box, your item WILL NOT include it.
                  </p>
                </div>
              )}
              
              {/* Price Summary */}
              <div className="border-t border-slate-700 pt-2 sm:pt-3">
                <div className="space-y-1">
                  <div className="flex justify-between text-xs sm:text-sm text-slate-400">
                    <span>Base Price:</span>
                    <span>${(selectedVariation?.price || selectedProduct.display_price || selectedProduct.price).toFixed(2)}</span>
                  </div>
                  {addHandle && (
                    <div className="flex justify-between text-xs sm:text-sm text-slate-400">
                      <span>Handle:</span>
                      <span>+$5.00</span>
                    </div>
                  )}
                  {addRank && (
                    <div className="flex justify-between text-xs sm:text-sm text-slate-400">
                      <span>Rank:</span>
                      <span>+$5.00</span>
                    </div>
                  )}
                  <div className="flex justify-between text-base sm:text-lg font-bold border-t border-slate-600 pt-2">
                    <span className="text-slate-200">Total:</span>
                    <span className="text-green-400">
                      ${calculateTotalPrice().toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <DialogFooter className="flex flex-col sm:flex-row gap-2">
            <Button variant="outline" onClick={() => setProductModalOpen(false)} className="border-slate-600 w-full sm:w-auto text-sm">
              Cancel
            </Button>
            <Button 
              onClick={handleConfirmAddToCart} 
              className="bg-blue-600 hover:bg-blue-700 w-full sm:w-auto text-sm"
              disabled={selectedProduct?.has_variations && !selectedVariation}
            >
              <ShoppingCart className="w-4 h-4 mr-2" />
              Add to Cart
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
