import { useState, useEffect, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  ArrowLeft,
  ShoppingCart,
  Package,
  Plus,
  Minus,
  Trash2,
  RefreshCw,
  Image as ImageIcon,
  LogIn,
  Lock,
} from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function SupporterStore() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [loading, setLoading] = useState(true);
  const [cartOpen, setCartOpen] = useState(false);
  const [redirectingToCheckout, setRedirectingToCheckout] = useState(false);
  
  // Store status
  const [storeOpen, setStoreOpen] = useState(true);
  
  // Product modal state
  const [productModalOpen, setProductModalOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [selectedVariation, setSelectedVariation] = useState(null);
  const [addHandle, setAddHandle] = useState(false);
  const [handleText, setHandleText] = useState("");
  const [addRank, setAddRank] = useState(false);
  const [rankText, setRankText] = useState("");
  
  // Customer info for checkout
  const [customerName, setCustomerName] = useState("");
  const [customerEmail, setCustomerEmail] = useState("");
  const [shippingAddress, setShippingAddress] = useState("");

  // Fetch store settings (public)
  const fetchStoreSettings = useCallback(async () => {
    try {
      const response = await axios.get(`${API_URL}/api/store/settings/public`);
      setStoreOpen(response.data.supporter_store_open);
    } catch (error) {
      console.error("Error fetching store settings:", error);
      // Default to open if we can't fetch settings
      setStoreOpen(true);
    }
  }, []);

  // Fetch supporter products (public endpoint)
  const fetchProducts = useCallback(async () => {
    try {
      const response = await axios.get(`${API_URL}/api/store/public/products`);
      setProducts(response.data);
    } catch (error) {
      toast.error("Failed to load products");
    }
  }, []);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchProducts(), fetchStoreSettings()]);
      setLoading(false);
    };
    loadData();
  }, [fetchProducts, fetchStoreSettings]);

  // Handle return from Square checkout
  useEffect(() => {
    const paymentStatus = searchParams.get("payment");
    const orderId = searchParams.get("order_id");
    
    if (paymentStatus === "success" && orderId) {
      toast.success("Payment successful! Thank you for your order.");
      // Clear cart and URL params after a brief delay to avoid cascading renders
      const timer = setTimeout(() => {
        setCart([]);
        setSearchParams({});
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [searchParams, setSearchParams]);

  // Cart calculations
  const cartTotal = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const cartCount = cart.reduce((sum, item) => sum + item.quantity, 0);

  const handleAddToCartClick = (product) => {
    if (product.has_variations) {
      setSelectedProduct(product);
      setSelectedVariation(null);
      setAddHandle(false);
      setHandleText("");
      setAddRank(false);
      setRankText("");
      setProductModalOpen(true);
    } else {
      addToCart(product, null, null, 0);
    }
  };

  const addToCart = (product, variation, customization, addOnPrice) => {
    const price = (variation?.price || product.display_price || product.price) + addOnPrice;
    const cartItem = {
      product_id: product.id,
      name: variation ? `${product.name} (${variation.name})` : product.name,
      variation_id: variation?.id || null,
      variation_name: variation?.name || null,
      price: price,
      quantity: 1,
      customization: customization,
      image_url: product.image_url,
    };

    // Check if item already in cart
    const existingIndex = cart.findIndex(
      (item) =>
        item.product_id === cartItem.product_id &&
        item.variation_id === cartItem.variation_id &&
        item.customization === cartItem.customization
    );

    if (existingIndex >= 0) {
      const newCart = [...cart];
      newCart[existingIndex].quantity += 1;
      setCart(newCart);
    } else {
      setCart([...cart, cartItem]);
    }

    toast.success("Added to cart!");
  };

  const handleConfirmAddToCart = () => {
    if (selectedProduct?.has_variations && !selectedVariation) {
      toast.error("Please select a size");
      return;
    }

    let customization = "";
    let addOnPrice = 0;

    if (selectedProduct?.allows_customization) {
      const parts = [];
      if (addHandle && handleText.trim()) {
        parts.push(`Handle: ${handleText.trim()}`);
        addOnPrice += 5;
      }
      if (addRank && rankText.trim()) {
        parts.push(`Rank: ${rankText.trim()}`);
        addOnPrice += 5;
      }
      customization = parts.join(", ");
    }

    addToCart(selectedProduct, selectedVariation, customization || null, addOnPrice);
    setProductModalOpen(false);
  };

  const updateCartItem = (index, quantity) => {
    if (quantity <= 0) {
      setCart(cart.filter((_, i) => i !== index));
    } else {
      const newCart = [...cart];
      newCart[index].quantity = quantity;
      setCart(newCart);
    }
  };

  const calculateTotalPrice = () => {
    const basePrice = selectedVariation?.price || selectedProduct?.display_price || selectedProduct?.price || 0;
    let addOnPrice = 0;
    if (addHandle) addOnPrice += 5;
    if (addRank) addOnPrice += 5;
    return basePrice + addOnPrice;
  };

  const handleCheckout = async () => {
    if (!customerName.trim() || !customerEmail.trim()) {
      toast.error("Please enter your name and email");
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(customerEmail)) {
      toast.error("Please enter a valid email address");
      return;
    }

    setRedirectingToCheckout(true);
    try {
      const response = await axios.post(`${API_URL}/api/store/public/checkout`, {
        items: cart,
        customer_name: customerName,
        customer_email: customerEmail,
        shipping_address: shippingAddress,
      });

      if (response.data.success && response.data.checkout_url) {
        setCartOpen(false);
        window.location.href = response.data.checkout_url;
      } else {
        toast.error("Failed to create checkout");
        setRedirectingToCheckout(false);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Checkout failed");
      setRedirectingToCheckout(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 p-2 sm:p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4 sm:mb-6">
          <div className="flex items-center justify-between sm:justify-start gap-2 sm:gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate("/login")}
              className="text-slate-300 hover:text-white px-2 sm:px-3"
            >
              <ArrowLeft className="w-4 h-4 sm:mr-2" />
              <span className="hidden sm:inline">Back</span>
            </Button>
            <h1 className="text-lg sm:text-2xl font-bold text-white flex items-center gap-2">
              <Package className="w-5 h-5 sm:w-6 sm:h-6" />
              Supporter Store
            </h1>
          </div>

          <div className="flex items-center justify-end gap-2 sm:gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate("/login")}
              className="border-slate-600 text-slate-300 hover:bg-slate-700"
            >
              <LogIn className="w-4 h-4 sm:mr-2" />
              <span className="hidden sm:inline">Member Login</span>
            </Button>
            <Button
              onClick={() => setCartOpen(true)}
              variant="outline"
              size="sm"
              className="relative border-slate-600 text-slate-200 hover:bg-slate-700"
            >
              <ShoppingCart className="w-4 h-4 sm:mr-2" />
              <span className="hidden sm:inline">Cart</span>
              {cartCount > 0 && (
                <Badge className="absolute -top-2 -right-2 bg-red-500 text-white text-xs px-1.5 min-w-[20px] h-5 flex items-center justify-center">
                  {cartCount}
                </Badge>
              )}
            </Button>
          </div>
        </div>

        {/* Supporter Banner */}
        <div className="bg-gradient-to-r from-green-900/50 to-blue-900/50 border border-green-700/50 rounded-lg p-3 sm:p-4 mb-4 sm:mb-6">
          <h2 className="text-green-400 font-semibold text-sm sm:text-base">Welcome, Supporter!</h2>
          <p className="text-slate-300 text-xs sm:text-sm mt-1">
            Browse and purchase supporter merchandise. Members can log in for additional items and dues payment.
          </p>
        </div>

        {/* Under Construction View */}
        {!storeOpen ? (
          <div className="flex flex-col items-center justify-center py-16 sm:py-24">
            <div className="bg-slate-800 border border-yellow-600/30 rounded-xl p-8 sm:p-12 text-center max-w-md">
              <div className="w-16 h-16 sm:w-20 sm:h-20 bg-yellow-600/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <Lock className="w-8 h-8 sm:w-10 sm:h-10 text-yellow-500" />
              </div>
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-2">Under Construction</h2>
              <p className="text-slate-400 text-sm sm:text-base mb-4">
                The Supporter Store is currently closed for maintenance. Please check back soon!
              </p>
              <Badge className="bg-yellow-600/20 text-yellow-400 border border-yellow-600/30">
                Coming Soon
              </Badge>
              <div className="mt-6">
                <Button
                  variant="outline"
                  onClick={() => navigate("/login")}
                  className="border-slate-600 text-slate-300 hover:bg-slate-700"
                >
                  <LogIn className="w-4 h-4 mr-2" />
                  Member Login
                </Button>
              </div>
            </div>
          </div>
        ) : (
        <>
        {/* Products Grid */}
        {products.length === 0 ? (
          <div className="text-center py-8 sm:py-12 text-slate-400">
            <Package className="w-10 h-10 sm:w-12 sm:h-12 mx-auto mb-4 opacity-50" />
            <p className="text-sm sm:text-base">No supporter merchandise available at this time.</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 sm:gap-4">
            {products.map((product) => (
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
                  <CardTitle className="text-white text-sm sm:text-base md:text-lg line-clamp-2">
                    {product.name}
                  </CardTitle>
                  {product.description && (
                    <CardDescription className="text-slate-400 text-xs sm:text-sm line-clamp-2 hidden sm:block">
                      {product.description}
                    </CardDescription>
                  )}
                </CardHeader>
                <CardContent className="p-2 sm:p-4 pt-0 flex-1">
                  <div className="mb-2">
                    <span className="text-base sm:text-xl font-bold text-white">
                      {product.has_variations
                        ? `From $${product.display_price.toFixed(2)}`
                        : `$${product.display_price.toFixed(2)}`}
                    </span>
                  </div>
                  <div className="text-xs sm:text-sm text-slate-400 mb-2">
                    {product.inventory_count > 0 ? (
                      <span className="text-green-400">{product.inventory_count} in stock</span>
                    ) : (
                      <span className="text-red-400">Out of stock</span>
                    )}
                  </div>
                  {product.has_variations && product.variations && (
                    <div className="hidden sm:flex flex-wrap gap-1 mb-2">
                      {product.variations.slice(0, 6).map((v) => (
                        <Badge
                          key={v.id}
                          variant="outline"
                          className={`text-[10px] sm:text-xs ${
                            v.sold_out || v.inventory_count === 0
                              ? "text-slate-500 border-slate-600 line-through"
                              : "text-slate-300 border-slate-500"
                          }`}
                        >
                          {v.name}
                        </Badge>
                      ))}
                    </div>
                  )}
                  {product.allows_customization && (
                    <Badge className="bg-purple-600 text-[10px] sm:text-xs">Add Handle</Badge>
                  )}
                </CardContent>
                <CardFooter className="p-2 sm:p-4 pt-0">
                  <Button
                    onClick={() => handleAddToCartClick(product)}
                    disabled={product.inventory_count === 0}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-xs sm:text-sm py-2"
                    size="sm"
                  >
                    <ShoppingCart className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2" />
                    {product.has_variations ? "Options" : "Add"}
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Cart Dialog */}
      <Dialog open={cartOpen} onOpenChange={setCartOpen}>
        <DialogContent className="bg-slate-800 border-slate-700 max-w-[95vw] sm:max-w-lg mx-2 sm:mx-auto max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2 text-base sm:text-lg">
              <ShoppingCart className="w-4 h-4 sm:w-5 sm:h-5" />
              Shopping Cart
            </DialogTitle>
          </DialogHeader>
          {cart.length === 0 ? (
            <div className="text-center py-6 sm:py-8 text-slate-400 text-sm sm:text-base">
              Your cart is empty
            </div>
          ) : (
            <>
              <div className="space-y-2 sm:space-y-3 max-h-48 sm:max-h-56 overflow-y-auto">
                {cart.map((item, idx) => (
                  <div
                    key={`${item.product_id}-${item.variation_id || ""}-${item.customization || ""}-${idx}`}
                    className="flex flex-col sm:flex-row sm:items-center justify-between p-2 sm:p-3 bg-slate-700 rounded-lg gap-2"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="text-white font-medium text-sm sm:text-base truncate">
                        {item.name}
                      </div>
                      <div className="text-slate-400 text-xs sm:text-sm">
                        ${item.price.toFixed(2)} each
                      </div>
                      {item.customization && (
                        <div className="text-purple-400 text-xs">{item.customization}</div>
                      )}
                    </div>
                    <div className="flex items-center gap-1 sm:gap-2 justify-end">
                      <Button
                        size="icon"
                        variant="outline"
                        onClick={() => updateCartItem(idx, item.quantity - 1)}
                        className="h-7 w-7 sm:h-8 sm:w-8 border-slate-600"
                      >
                        <Minus className="w-3 h-3" />
                      </Button>
                      <span className="text-white w-6 sm:w-8 text-center text-sm">
                        {item.quantity}
                      </span>
                      <Button
                        size="icon"
                        variant="outline"
                        onClick={() => updateCartItem(idx, item.quantity + 1)}
                        className="h-7 w-7 sm:h-8 sm:w-8 border-slate-600"
                      >
                        <Plus className="w-3 h-3" />
                      </Button>
                      <Button
                        size="icon"
                        variant="ghost"
                        onClick={() => updateCartItem(idx, 0)}
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
                  <span>${cartTotal.toFixed(2)}</span>
                </div>
                <div className="text-xs text-slate-400">+ Tax calculated at checkout</div>
                
                {/* Customer Info */}
                <div className="space-y-2 pt-2 border-t border-slate-700">
                  <div>
                    <Label className="text-slate-200 text-xs sm:text-sm">
                      Name <span className="text-red-400">*</span>
                    </Label>
                    <Input
                      value={customerName}
                      onChange={(e) => setCustomerName(e.target.value)}
                      placeholder="Your name"
                      className="bg-slate-700 border-slate-600 text-white mt-1 text-sm"
                    />
                  </div>
                  <div>
                    <Label className="text-slate-200 text-xs sm:text-sm">
                      Email <span className="text-red-400">*</span>
                    </Label>
                    <Input
                      type="email"
                      value={customerEmail}
                      onChange={(e) => setCustomerEmail(e.target.value)}
                      placeholder="your@email.com"
                      className="bg-slate-700 border-slate-600 text-white mt-1 text-sm"
                    />
                  </div>
                  <div>
                    <Label className="text-slate-200 text-xs sm:text-sm">
                      Shipping Address
                    </Label>
                    <Textarea
                      value={shippingAddress}
                      onChange={(e) => setShippingAddress(e.target.value)}
                      placeholder="Enter shipping address..."
                      className="bg-slate-700 border-slate-600 text-white mt-1 text-sm"
                      rows={2}
                    />
                  </div>
                </div>
              </div>
            </>
          )}
          <DialogFooter className="flex flex-col sm:flex-row gap-2">
            <Button
              variant="outline"
              onClick={() => setCart([])}
              className="border-slate-600 text-sm w-full sm:w-auto"
              disabled={redirectingToCheckout || cart.length === 0}
            >
              Clear Cart
            </Button>
            <Button
              onClick={handleCheckout}
              disabled={cart.length === 0 || redirectingToCheckout}
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

      {/* Product Options Modal */}
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
                  <Label className="text-slate-200 mb-2 block text-xs sm:text-sm">
                    Select Size *
                  </Label>
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
                          ${
                            selectedVariation?.id === variation.id
                              ? "bg-blue-600 text-white"
                              : "border-slate-600 text-slate-300 hover:bg-slate-700"
                          }
                          ${(variation.sold_out || variation.inventory_count === 0) && "opacity-50 line-through"}
                        `}
                      >
                        {variation.name}
                      </Button>
                    ))}
                  </div>
                  {selectedVariation && (
                    <div className="mt-2 text-xs sm:text-sm text-slate-400">
                      Price:{" "}
                      <span className="text-green-400 font-bold">
                        ${selectedVariation.price.toFixed(2)}
                      </span>
                      {selectedVariation.inventory_count > 0 && (
                        <span className="ml-2">({selectedVariation.inventory_count} in stock)</span>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Customization Options */}
              {selectedProduct.allows_customization && (
                <div className="space-y-2 sm:space-y-3 border border-slate-600 rounded-lg p-2 sm:p-4 bg-slate-700/30">
                  <Label className="text-slate-200 font-semibold block text-xs sm:text-sm">
                    Add Text
                  </Label>

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
                        className="w-4 h-4 rounded border-slate-500 bg-slate-700 text-blue-600"
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
                        className="w-4 h-4 rounded border-slate-500 bg-slate-700 text-blue-600"
                      />
                      <label htmlFor="addRank" className="text-slate-300 flex-1 text-xs sm:text-sm">
                        Add your Rank{" "}
                        <span className="text-slate-500 text-[10px] sm:text-xs">
                          (Officer&apos;s Only)
                        </span>
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
                    ⚠️ If you add your rank or handle without checking the box, your item WILL NOT
                    include it.
                  </p>
                </div>
              )}

              {/* Price Summary */}
              <div className="border-t border-slate-700 pt-2 sm:pt-3">
                <div className="space-y-1">
                  <div className="flex justify-between text-xs sm:text-sm text-slate-400">
                    <span>Base Price:</span>
                    <span>
                      $
                      {(
                        selectedVariation?.price ||
                        selectedProduct.display_price ||
                        selectedProduct.price
                      ).toFixed(2)}
                    </span>
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
                    <span className="text-green-400">${calculateTotalPrice().toFixed(2)}</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          <DialogFooter className="flex flex-col sm:flex-row gap-2">
            <Button
              variant="outline"
              onClick={() => setProductModalOpen(false)}
              className="border-slate-600 w-full sm:w-auto text-sm"
            >
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
