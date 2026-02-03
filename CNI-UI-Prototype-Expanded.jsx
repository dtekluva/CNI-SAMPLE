import React, { useState } from 'react';
import { Car, Calendar, Users, Wrench, DollarSign, BarChart3, Settings, Menu, Bell, Search, MapPin,
         ChevronRight, CheckCircle, AlertTriangle, XCircle, Plus, Filter, Download, Upload, Edit,
         Trash2, Eye, X, Clock, Phone, Mail, User, CreditCard, FileText, Camera, CheckSquare,
         AlertCircle, RefreshCw, Send, Printer, MessageSquare, CalendarDays, ChevronLeft, Check } from 'lucide-react';

const CNIFleetManagementUI = () => {
  const [currentView, setCurrentView] = useState('bookings');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [bookingsSubView, setBookingsSubView] = useState('list'); // list, new, details, calendar
  const [selectedBooking, setSelectedBooking] = useState(null);
  const [newBookingStep, setNewBookingStep] = useState(1);
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState(null);
  const [filterStatus, setFilterStatus] = useState('all');

  // Enhanced booking form state
  const [bookingForm, setBookingForm] = useState({
    customer: null,
    vehicleType: '',
    startDate: '',
    endDate: '',
    pickupTime: '',
    returnTime: '',
    withDriver: false,
    insurance: false,
    notes: '',
    totalDays: 0,
    baseRate: 0,
    driverFee: 0,
    insuranceFee: 0,
    discount: 0,
    totalAmount: 0
  });

  // Color palette
  const colors = {
    primary: '#1F4788',
    secondary: '#2E5C8A',
    accent: '#3A6B8F',
    success: '#28A745',
    warning: '#FFC107',
    danger: '#DC3545',
    info: '#17A2B8',
    darkGrey: '#343A40',
    mediumGrey: '#6C757D',
    lightGrey: '#E9ECEF',
    white: '#FFFFFF',
  };

  // Enhanced sample data - Bookings
  const allBookings = [
    {
      id: 'BK-2401',
      vehicle: { name: 'Toyota Camry 2023', id: 'LA-001', type: 'Sedan' },
      customer: { name: 'Acme Corporation', contact: 'Mr. Adeyemi', phone: '0803-123-4567', email: 'adeyemi@acmecorp.ng' },
      status: 'active',
      startDate: '2026-01-15',
      endDate: '2026-01-20',
      days: 5,
      amount: '₦147,813',
      withDriver: true,
      driver: 'John Obi',
      paymentStatus: 'paid',
      bookingType: 'corporate'
    },
    {
      id: 'BK-2400',
      vehicle: { name: 'Honda Accord 2022', id: 'LA-002', type: 'Sedan' },
      customer: { name: 'John Doe', contact: 'John Doe', phone: '0805-987-6543', email: 'john.doe@email.com' },
      status: 'completed',
      startDate: '2026-01-10',
      endDate: '2026-01-14',
      days: 4,
      amount: '₦85,000',
      withDriver: false,
      driver: null,
      paymentStatus: 'paid',
      bookingType: 'walk-in'
    },
    {
      id: 'BK-2399',
      vehicle: { name: 'Lexus RX350 2024', id: 'LA-003', type: 'SUV' },
      customer: { name: 'TechCo Nigeria', contact: 'Ms. Okonkwo', phone: '0807-555-1234', email: 'procurement@techco.ng' },
      status: 'confirmed',
      startDate: '2026-01-18',
      endDate: '2026-01-25',
      days: 7,
      amount: '₦280,000',
      withDriver: true,
      driver: 'Ada Eze',
      paymentStatus: 'pending',
      bookingType: 'contract'
    },
    {
      id: 'BK-2398',
      vehicle: { name: 'Toyota Hilux 2023', id: 'LA-004', type: 'Truck' },
      customer: { name: 'BuildCo Ltd', contact: 'Engr. Ibrahim', phone: '0809-444-7890', email: 'ibrahim@buildco.ng' },
      status: 'pending',
      startDate: '2026-01-20',
      endDate: '2026-01-27',
      days: 7,
      amount: '₦210,000',
      withDriver: true,
      driver: 'Pending Assignment',
      paymentStatus: 'awaiting',
      bookingType: 'corporate'
    },
    {
      id: 'BK-2397',
      vehicle: { name: 'Mercedes C-Class 2024', id: 'LA-005', type: 'Sedan' },
      customer: { name: 'Law Firm Associates', contact: 'Mrs. Nwosu', phone: '0802-333-9876', email: 'nwosu@lawfirm.ng' },
      status: 'cancelled',
      startDate: '2026-01-11',
      endDate: '2026-01-15',
      days: 4,
      amount: '₦180,000',
      withDriver: false,
      driver: null,
      paymentStatus: 'refunded',
      bookingType: 'corporate'
    },
    {
      id: 'BK-2396',
      vehicle: { name: 'Toyota Corolla 2022', id: 'LA-006', type: 'Sedan' },
      customer: { name: 'Wedding Events Ltd', contact: 'Mr. Chukwu', phone: '0808-222-5432', email: 'chukwu@weddings.ng' },
      status: 'active',
      startDate: '2026-01-16',
      endDate: '2026-01-16',
      days: 1,
      amount: '₦35,000',
      withDriver: true,
      driver: 'Chidi Okoro',
      paymentStatus: 'paid',
      bookingType: 'walk-in'
    },
  ];

  // Available vehicles for booking
  const availableVehicles = [
    { id: 'LA-002', name: 'Honda Accord 2022', type: 'Sedan', rate: 20000, seats: 5, image: '🚗', features: ['AC', 'GPS', 'Bluetooth'] },
    { id: 'LA-005', name: 'Mercedes C-Class 2024', type: 'Sedan', rate: 45000, seats: 5, image: '🚗', features: ['AC', 'GPS', 'Leather', 'Sunroof'] },
    { id: 'LA-007', name: 'Toyota Prado 2023', type: 'SUV', rate: 55000, seats: 7, image: '🚙', features: ['AC', 'GPS', '4WD', 'Leather'] },
    { id: 'LA-008', name: 'Honda CR-V 2023', type: 'SUV', rate: 40000, seats: 5, image: '🚙', features: ['AC', 'GPS', 'Backup Camera'] },
    { id: 'LA-009', name: 'Toyota Hiace 2023', type: 'Bus', rate: 60000, seats: 14, image: '🚐', features: ['AC', 'GPS', 'High Roof'] },
    { id: 'LA-010', name: 'Ford Ranger 2023', type: 'Truck', rate: 50000, seats: 5, image: '🚚', features: ['AC', '4WD', 'Cargo Bed'] },
  ];

  // Customers database
  const customers = [
    { id: 'C-001', name: 'Acme Corporation', type: 'Corporate', contact: 'Mr. Adeyemi', phone: '0803-123-4567', email: 'adeyemi@acmecorp.ng' },
    { id: 'C-002', name: 'TechCo Nigeria', type: 'Contract', contact: 'Ms. Okonkwo', phone: '0807-555-1234', email: 'procurement@techco.ng' },
    { id: 'C-003', name: 'BuildCo Ltd', type: 'Corporate', contact: 'Engr. Ibrahim', phone: '0809-444-7890', email: 'ibrahim@buildco.ng' },
    { id: 'C-004', name: 'Law Firm Associates', type: 'Corporate', contact: 'Mrs. Nwosu', phone: '0802-333-9876', email: 'nwosu@lawfirm.ng' },
  ];

  // Filter bookings by status
  const filteredBookings = filterStatus === 'all'
    ? allBookings
    : allBookings.filter(b => b.status === filterStatus);

  // Navigation items
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3, badge: null },
    { id: 'bookings', label: 'Bookings & Reservations', icon: Calendar, badge: 15 },
    { id: 'fleet', label: 'Fleet Management', icon: Car, badge: null },
    { id: 'clients', label: 'Clients & Contracts', icon: Users, badge: null },
    { id: 'maintenance', label: 'Maintenance', icon: Wrench, badge: 3 },
    { id: 'invoicing', label: 'Invoicing & Payments', icon: DollarSign, badge: 5 },
    { id: 'reports', label: 'Reports & Analytics', icon: BarChart3, badge: null },
    { id: 'settings', label: 'Settings', icon: Settings, badge: null },
  ];

  // Status badge component
  const StatusBadge = ({ status }) => {
    const statusConfig = {
      pending: { bg: '#FFF3CD', text: '#856404', label: 'Pending', icon: '⏳' },
      confirmed: { bg: '#D1ECF1', text: '#0C5460', label: 'Confirmed', icon: '✓' },
      active: { bg: '#D4EDDA', text: '#155724', label: 'Active', icon: '🔵' },
      completed: { bg: '#D4EDDA', text: '#155724', label: 'Completed', icon: '✅' },
      cancelled: { bg: '#F8D7DA', text: '#721C24', label: 'Cancelled', icon: '❌' },
    };

    const config = statusConfig[status] || statusConfig.pending;

    return (
      <span style={{
        backgroundColor: config.bg,
        color: config.text,
        padding: '4px 12px',
        borderRadius: '12px',
        fontSize: '12px',
        fontWeight: '600',
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
      }}>
        <span>{config.icon}</span>
        {config.label}
      </span>
    );
  };

  // Payment status badge
  const PaymentBadge = ({ status }) => {
    const statusConfig = {
      paid: { bg: '#D4EDDA', text: '#155724', label: 'Paid', icon: '✓' },
      pending: { bg: '#FFF3CD', text: '#856404', label: 'Pending', icon: '⏳' },
      awaiting: { bg: '#FFE8CC', text: '#8B5000', label: 'Awaiting', icon: '⏱' },
      refunded: { bg: '#E8E8E8', text: '#505050', label: 'Refunded', icon: '↩' },
    };

    const config = statusConfig[status] || statusConfig.pending;

    return (
      <span style={{
        backgroundColor: config.bg,
        color: config.text,
        padding: '4px 10px',
        borderRadius: '12px',
        fontSize: '11px',
        fontWeight: '600',
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
      }}>
        <span>{config.icon}</span>
        {config.label}
      </span>
    );
  };

  // Button component
  const Button = ({ children, onClick, variant = 'primary', icon: Icon, size = 'medium', disabled = false }) => {
    const variants = {
      primary: { bg: colors.primary, color: colors.white, border: 'none' },
      secondary: { bg: colors.white, color: colors.primary, border: `1px solid ${colors.primary}` },
      danger: { bg: colors.danger, color: colors.white, border: 'none' },
      success: { bg: colors.success, color: colors.white, border: 'none' },
      ghost: { bg: 'transparent', color: colors.mediumGrey, border: `1px solid ${colors.lightGrey}` },
    };

    const sizes = {
      small: { padding: '6px 12px', fontSize: '13px' },
      medium: { padding: '10px 20px', fontSize: '14px' },
      large: { padding: '12px 24px', fontSize: '15px' },
    };

    const style = {
      ...variants[variant],
      ...sizes[size],
      borderRadius: '8px',
      cursor: disabled ? 'not-allowed' : 'pointer',
      fontWeight: '600',
      display: 'inline-flex',
      alignItems: 'center',
      gap: '8px',
      transition: 'all 0.2s',
      opacity: disabled ? 0.5 : 1,
    };

    return (
      <button onClick={onClick} style={style} disabled={disabled}>
        {Icon && <Icon size={16} />}
        {children}
      </button>
    );
  };

  // Modal component
  const Modal = ({ isOpen, onClose, title, children, width = '600px' }) => {
    if (!isOpen) return null;

    return (
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0,0,0,0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 2000,
      }}>
        <div style={{
          backgroundColor: colors.white,
          borderRadius: '12px',
          width,
          maxWidth: '90vw',
          maxHeight: '90vh',
          overflow: 'auto',
          boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
        }}>
          <div style={{
            padding: '24px',
            borderBottom: `1px solid ${colors.lightGrey}`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <h3 style={{ margin: 0, fontSize: '20px', fontWeight: '700', color: colors.darkGrey }}>{title}</h3>
            <button
              onClick={onClose}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                padding: '4px',
                display: 'flex',
                alignItems: 'center',
                borderRadius: '4px',
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = colors.lightGrey}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
            >
              <X size={20} color={colors.mediumGrey} />
            </button>
          </div>
          <div style={{ padding: '24px' }}>
            {children}
          </div>
        </div>
      </div>
    );
  };

  // Sidebar component
  const Sidebar = () => (
    <div style={{
      width: sidebarOpen ? '280px' : '0',
      backgroundColor: colors.darkGrey,
      height: '100vh',
      position: 'fixed',
      left: 0,
      top: 0,
      transition: 'width 0.3s ease',
      overflow: 'hidden',
      zIndex: 1000,
      boxShadow: '2px 0 8px rgba(0,0,0,0.1)',
    }}>
      <div style={{ padding: '24px 20px', borderBottom: `1px solid ${colors.mediumGrey}` }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '40px',
            height: '40px',
            backgroundColor: colors.primary,
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: colors.white,
            fontWeight: '700',
            fontSize: '18px',
          }}>
            CNI
          </div>
          <div>
            <h2 style={{ color: colors.white, margin: 0, fontSize: '18px', fontWeight: '700' }}>CNI Fleet</h2>
            <p style={{ color: colors.mediumGrey, margin: 0, fontSize: '12px' }}>Management System</p>
          </div>
        </div>
      </div>
      <nav style={{ padding: '10px 0' }}>
        {navItems.map(item => (
          <button
            key={item.id}
            onClick={() => {
              setCurrentView(item.id);
              if (item.id === 'bookings') setBookingsSubView('list');
            }}
            style={{
              width: '100%',
              padding: '14px 20px',
              backgroundColor: currentView === item.id ? colors.primary : 'transparent',
              color: colors.white,
              border: 'none',
              textAlign: 'left',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              transition: 'all 0.2s',
              borderLeft: currentView === item.id ? `4px solid ${colors.accent}` : '4px solid transparent',
            }}
            onMouseEnter={(e) => {
              if (currentView !== item.id) {
                e.currentTarget.style.backgroundColor = colors.secondary;
                e.currentTarget.style.borderLeft = `4px solid ${colors.secondary}`;
              }
            }}
            onMouseLeave={(e) => {
              if (currentView !== item.id) {
                e.currentTarget.style.backgroundColor = 'transparent';
                e.currentTarget.style.borderLeft = '4px solid transparent';
              }
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <item.icon size={20} />
              <span style={{ fontSize: '14px' }}>{item.label}</span>
            </div>
            {item.badge && (
              <span style={{
                backgroundColor: colors.danger,
                color: colors.white,
                padding: '2px 8px',
                borderRadius: '10px',
                fontSize: '11px',
                fontWeight: '600',
              }}>
                {item.badge}
              </span>
            )}
          </button>
        ))}
      </nav>
    </div>
  );

  // Header component
  const Header = () => (
    <div style={{
      height: '70px',
      backgroundColor: colors.white,
      borderBottom: `1px solid ${colors.lightGrey}`,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 32px',
      position: 'fixed',
      top: 0,
      left: sidebarOpen ? '280px' : '0',
      right: 0,
      zIndex: 999,
      transition: 'left 0.3s ease',
      boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '8px',
            display: 'flex',
            alignItems: 'center',
            borderRadius: '6px',
          }}
          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = colors.lightGrey}
          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
        >
          <Menu size={24} color={colors.darkGrey} />
        </button>
        <div>
          <h1 style={{ fontSize: '22px', margin: 0, color: colors.darkGrey, fontWeight: '700' }}>
            {currentView === 'bookings' ? 'Bookings & Reservations' : navItems.find(item => item.id === currentView)?.label}
          </h1>
          <p style={{ fontSize: '13px', margin: '4px 0 0 0', color: colors.mediumGrey }}>
            {currentView === 'bookings' ? 'Manage vehicle bookings and reservations' : 'Manage and monitor'}
          </p>
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          backgroundColor: colors.lightGrey,
          borderRadius: '8px',
          padding: '8px 16px',
          gap: '8px',
        }}>
          <Search size={18} color={colors.mediumGrey} />
          <input
            type="text"
            placeholder="Quick search..."
            style={{
              border: 'none',
              outline: 'none',
              backgroundColor: 'transparent',
              fontSize: '14px',
              width: '200px',
            }}
          />
        </div>
        <button style={{
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          position: 'relative',
          padding: '8px',
          borderRadius: '6px',
        }}
        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = colors.lightGrey}
        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
        >
          <Bell size={22} color={colors.darkGrey} />
          <span style={{
            position: 'absolute',
            top: '4px',
            right: '4px',
            backgroundColor: colors.danger,
            color: colors.white,
            borderRadius: '50%',
            width: '20px',
            height: '20px',
            fontSize: '11px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: '600',
            border: `2px solid ${colors.white}`,
          }}>3</span>
        </button>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}>
          <div>
            <div style={{ fontSize: '14px', fontWeight: '600', color: colors.darkGrey, textAlign: 'right' }}>Otimeyin Afolabi</div>
            <div style={{ fontSize: '12px', color: colors.mediumGrey, textAlign: 'right' }}>Administrator</div>
          </div>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '50%',
            backgroundColor: colors.primary,
            color: colors.white,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: '700',
            fontSize: '16px',
            border: `2px solid ${colors.lightGrey}`,
          }}>
            OA
          </div>
        </div>
      </div>
    </div>
  );

  // BOOKINGS LIST VIEW
  const BookingsListView = () => (
    <div style={{ padding: '32px' }}>
      {/* Actions Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '28px' }}>
        <div style={{ display: 'flex', gap: '12px', flex: 1 }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            backgroundColor: colors.white,
            border: `1px solid ${colors.lightGrey}`,
            borderRadius: '8px',
            padding: '10px 16px',
            gap: '10px',
            width: '400px',
          }}>
            <Search size={18} color={colors.mediumGrey} />
            <input
              type="text"
              placeholder="Search by booking ID, customer, or vehicle..."
              style={{
                border: 'none',
                outline: 'none',
                flex: 1,
                fontSize: '14px',
              }}
            />
          </div>

          {/* Status Filter Tabs */}
          <div style={{ display: 'flex', gap: '8px', backgroundColor: colors.white, padding: '6px', borderRadius: '8px', border: `1px solid ${colors.lightGrey}` }}>
            {['all', 'pending', 'confirmed', 'active', 'completed', 'cancelled'].map(status => (
              <button
                key={status}
                onClick={() => setFilterStatus(status)}
                style={{
                  padding: '6px 16px',
                  backgroundColor: filterStatus === status ? colors.primary : 'transparent',
                  color: filterStatus === status ? colors.white : colors.mediumGrey,
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '13px',
                  fontWeight: '600',
                  textTransform: 'capitalize',
                  transition: 'all 0.2s',
                }}
              >
                {status} {status === 'all' && `(${allBookings.length})`}
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <Button variant="ghost" icon={CalendarDays} onClick={() => setBookingsSubView('calendar')}>
            Calendar View
          </Button>
          <Button variant="ghost" icon={Download}>
            Export
          </Button>
          <Button icon={Plus} onClick={() => {
            setBookingsSubView('new');
            setNewBookingStep(1);
          }}>
            New Booking
          </Button>
        </div>
      </div>

      {/* Bookings Table */}
      <div style={{
        backgroundColor: colors.white,
        borderRadius: '12px',
        border: `1px solid ${colors.lightGrey}`,
        overflow: 'hidden',
        boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
      }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ backgroundColor: '#F8F9FA', borderBottom: `2px solid ${colors.lightGrey}` }}>
              <th style={{ padding: '16px 20px', textAlign: 'left', fontSize: '13px', fontWeight: '700', color: colors.darkGrey, textTransform: 'uppercase' }}>Booking ID</th>
              <th style={{ padding: '16px 20px', textAlign: 'left', fontSize: '13px', fontWeight: '700', color: colors.darkGrey, textTransform: 'uppercase' }}>Customer</th>
              <th style={{ padding: '16px 20px', textAlign: 'left', fontSize: '13px', fontWeight: '700', color: colors.darkGrey, textTransform: 'uppercase' }}>Vehicle</th>
              <th style={{ padding: '16px 20px', textAlign: 'left', fontSize: '13px', fontWeight: '700', color: colors.darkGrey, textTransform: 'uppercase' }}>Period</th>
              <th style={{ padding: '16px 20px', textAlign: 'left', fontSize: '13px', fontWeight: '700', color: colors.darkGrey, textTransform: 'uppercase' }}>Status</th>
              <th style={{ padding: '16px 20px', textAlign: 'left', fontSize: '13px', fontWeight: '700', color: colors.darkGrey, textTransform: 'uppercase' }}>Payment</th>
              <th style={{ padding: '16px 20px', textAlign: 'right', fontSize: '13px', fontWeight: '700', color: colors.darkGrey, textTransform: 'uppercase' }}>Amount</th>
              <th style={{ padding: '16px 20px', textAlign: 'center', fontSize: '13px', fontWeight: '700', color: colors.darkGrey, textTransform: 'uppercase' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredBookings.map((booking, idx) => (
              <tr key={booking.id} style={{
                borderBottom: `1px solid ${colors.lightGrey}`,
                backgroundColor: idx % 2 === 0 ? colors.white : '#FAFBFC',
                transition: 'background-color 0.2s',
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#F0F4F8'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = idx % 2 === 0 ? colors.white : '#FAFBFC'}
              >
                <td style={{ padding: '16px 20px' }}>
                  <div style={{ fontSize: '14px', fontWeight: '700', color: colors.primary }}>{booking.id}</div>
                  <div style={{ fontSize: '11px', color: colors.mediumGrey, marginTop: '2px', textTransform: 'uppercase' }}>
                    {booking.bookingType}
                  </div>
                </td>
                <td style={{ padding: '16px 20px' }}>
                  <div style={{ fontSize: '14px', fontWeight: '600', color: colors.darkGrey }}>{booking.customer.name}</div>
                  <div style={{ fontSize: '12px', color: colors.mediumGrey, marginTop: '2px' }}>{booking.customer.phone}</div>
                </td>
                <td style={{ padding: '16px 20px' }}>
                  <div style={{ fontSize: '14px', color: colors.darkGrey }}>{booking.vehicle.name}</div>
                  <div style={{ fontSize: '12px', color: colors.mediumGrey, marginTop: '2px' }}>
                    {booking.withDriver ? `🚗 With Driver: ${booking.driver}` : '🔑 Self-Drive'}
                  </div>
                </td>
                <td style={{ padding: '16px 20px' }}>
                  <div style={{ fontSize: '13px', color: colors.darkGrey }}>{booking.startDate}</div>
                  <div style={{ fontSize: '13px', color: colors.darkGrey }}>to {booking.endDate}</div>
                  <div style={{ fontSize: '11px', color: colors.mediumGrey, marginTop: '2px' }}>({booking.days} days)</div>
                </td>
                <td style={{ padding: '16px 20px' }}>
                  <StatusBadge status={booking.status} />
                </td>
                <td style={{ padding: '16px 20px' }}>
                  <PaymentBadge status={booking.paymentStatus} />
                </td>
                <td style={{ padding: '16px 20px', textAlign: 'right' }}>
                  <div style={{ fontSize: '16px', fontWeight: '700', color: colors.darkGrey }}>{booking.amount}</div>
                </td>
                <td style={{ padding: '16px 20px', textAlign: 'center' }}>
                  <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
                    <button
                      onClick={() => {
                        setSelectedBooking(booking);
                        setBookingsSubView('details');
                      }}
                      style={{
                        padding: '6px 10px',
                        backgroundColor: 'transparent',
                        border: `1px solid ${colors.lightGrey}`,
                        borderRadius: '6px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                      }}
                      title="View Details"
                    >
                      <Eye size={16} color={colors.mediumGrey} />
                    </button>
                    <button style={{
                      padding: '6px 10px',
                      backgroundColor: 'transparent',
                      border: `1px solid ${colors.lightGrey}`,
                      borderRadius: '6px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                    }}
                    title="Edit"
                    >
                      <Edit size={16} color={colors.mediumGrey} />
                    </button>
                    <button style={{
                      padding: '6px 10px',
                      backgroundColor: 'transparent',
                      border: `1px solid ${colors.lightGrey}`,
                      borderRadius: '6px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                    }}
                    title="More Actions"
                    >
                      <ChevronRight size={16} color={colors.mediumGrey} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Pagination */}
        <div style={{
          padding: '16px 20px',
          borderTop: `1px solid ${colors.lightGrey}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: '#FAFBFC',
        }}>
          <div style={{ fontSize: '13px', color: colors.mediumGrey }}>
            Showing <strong>{filteredBookings.length}</strong> of <strong>{allBookings.length}</strong> bookings
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button style={{
              padding: '6px 12px',
              backgroundColor: colors.white,
              border: `1px solid ${colors.lightGrey}`,
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: '500',
            }}>Previous</button>
            <button style={{
              padding: '6px 12px',
              backgroundColor: colors.primary,
              color: colors.white,
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: '600',
            }}>1</button>
            <button style={{
              padding: '6px 12px',
              backgroundColor: colors.white,
              border: `1px solid ${colors.lightGrey}`,
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: '500',
            }}>2</button>
            <button style={{
              padding: '6px 12px',
              backgroundColor: colors.white,
              border: `1px solid ${colors.lightGrey}`,
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: '500',
            }}>Next</button>
          </div>
        </div>
      </div>
    </div>
  );

  // NEW BOOKING WIZARD - STEP 1: Customer Selection
  const NewBookingStep1 = () => (
    <div>
      <h3 style={{ fontSize: '18px', fontWeight: '700', color: colors.darkGrey, marginBottom: '8px' }}>
        Step 1: Select Customer
      </h3>
      <p style={{ fontSize: '14px', color: colors.mediumGrey, marginBottom: '24px' }}>
        Search for an existing customer or add a new one
      </p>

      <div style={{ marginBottom: '24px' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          backgroundColor: colors.lightGrey,
          borderRadius: '8px',
          padding: '12px 16px',
          gap: '10px',
          marginBottom: '20px',
        }}>
          <Search size={18} color={colors.mediumGrey} />
          <input
            type="text"
            placeholder="Search by name, company, phone, or email..."
            style={{
              border: 'none',
              outline: 'none',
              backgroundColor: 'transparent',
              flex: 1,
              fontSize: '14px',
            }}
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
          {customers.map(customer => (
            <div
              key={customer.id}
              onClick={() => {
                setBookingForm({ ...bookingForm, customer });
                setNewBookingStep(2);
              }}
              style={{
                padding: '16px',
                backgroundColor: colors.white,
                border: `2px solid ${colors.lightGrey}`,
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = colors.primary;
                e.currentTarget.style.backgroundColor = '#F8F9FA';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = colors.lightGrey;
                e.currentTarget.style.backgroundColor = colors.white;
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <div>
                  <div style={{ fontSize: '15px', fontWeight: '700', color: colors.darkGrey, marginBottom: '4px' }}>
                    {customer.name}
                  </div>
                  <div style={{ fontSize: '12px', color: colors.mediumGrey, marginBottom: '2px' }}>
                    {customer.contact}
                  </div>
                  <div style={{ fontSize: '12px', color: colors.mediumGrey }}>
                    📞 {customer.phone}
                  </div>
                  <div style={{ fontSize: '12px', color: colors.mediumGrey }}>
                    ✉️ {customer.email}
                  </div>
                </div>
                <span style={{
                  padding: '4px 8px',
                  backgroundColor: customer.type === 'Contract' ? '#D1ECF1' : '#FFF3CD',
                  color: customer.type === 'Contract' ? '#0C5460' : '#856404',
                  borderRadius: '4px',
                  fontSize: '11px',
                  fontWeight: '600',
                }}>
                  {customer.type}
                </span>
              </div>
            </div>
          ))}
        </div>

        <div style={{ marginTop: '20px', textAlign: 'center' }}>
          <Button variant="secondary" icon={Plus}>
            Add New Customer
          </Button>
        </div>
      </div>
    </div>
  );

  // NEW BOOKING WIZARD - STEP 2: Vehicle Selection
  const NewBookingStep2 = () => (
    <div>
      <h3 style={{ fontSize: '18px', fontWeight: '700', color: colors.darkGrey, marginBottom: '8px' }}>
        Step 2: Select Vehicle & Dates
      </h3>
      <p style={{ fontSize: '14px', color: colors.mediumGrey, marginBottom: '24px' }}>
        Choose from available vehicles for your selected dates
      </p>

      {/* Date Selection */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: '16px',
        marginBottom: '24px',
        padding: '20px',
        backgroundColor: '#F8F9FA',
        borderRadius: '8px',
      }}>
        <div>
          <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: colors.darkGrey, marginBottom: '8px' }}>
            Pickup Date & Time
          </label>
          <input
            type="date"
            value={bookingForm.startDate}
            onChange={(e) => setBookingForm({ ...bookingForm, startDate: e.target.value })}
            style={{
              width: '100%',
              padding: '10px',
              border: `1px solid ${colors.lightGrey}`,
              borderRadius: '6px',
              fontSize: '14px',
            }}
          />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: colors.darkGrey, marginBottom: '8px' }}>
            Return Date & Time
          </label>
          <input
            type="date"
            value={bookingForm.endDate}
            onChange={(e) => setBookingForm({ ...bookingForm, endDate: e.target.value })}
            style={{
              width: '100%',
              padding: '10px',
              border: `1px solid ${colors.lightGrey}`,
              borderRadius: '6px',
              fontSize: '14px',
            }}
          />
        </div>
      </div>

      {/* Vehicle Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
        {availableVehicles.map(vehicle => (
          <div
            key={vehicle.id}
            onClick={() => {
              setBookingForm({ ...bookingForm, vehicleType: vehicle.type, baseRate: vehicle.rate });
              setNewBookingStep(3);
            }}
            style={{
              padding: '16px',
              backgroundColor: colors.white,
              border: `2px solid ${colors.lightGrey}`,
              borderRadius: '12px',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = colors.primary;
              e.currentTarget.style.transform = 'translateY(-4px)';
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = colors.lightGrey;
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = 'none';
            }}
          >
            <div style={{ fontSize: '48px', textAlign: 'center', marginBottom: '12px' }}>
              {vehicle.image}
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '15px', fontWeight: '700', color: colors.darkGrey, marginBottom: '4px' }}>
                {vehicle.name}
              </div>
              <div style={{ fontSize: '12px', color: colors.mediumGrey, marginBottom: '8px' }}>
                {vehicle.seats} Seats • {vehicle.type}
              </div>
              <div style={{
                padding: '6px 0',
                borderTop: `1px solid ${colors.lightGrey}`,
                borderBottom: `1px solid ${colors.lightGrey}`,
                marginBottom: '8px',
              }}>
                <div style={{ fontSize: '20px', fontWeight: '700', color: colors.primary }}>
                  ₦{vehicle.rate.toLocaleString()}
                </div>
                <div style={{ fontSize: '11px', color: colors.mediumGrey }}>per day</div>
              </div>
              <div style={{ fontSize: '11px', color: colors.mediumGrey }}>
                {vehicle.features.join(' • ')}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div style={{ marginTop: '24px', display: 'flex', gap: '12px', justifyContent: 'space-between' }}>
        <Button variant="secondary" icon={ChevronLeft} onClick={() => setNewBookingStep(1)}>
          Back
        </Button>
      </div>
    </div>
  );

  // NEW BOOKING WIZARD - STEP 3: Add-ons & Summary
  const NewBookingStep3 = () => {
    const totalDays = 5; // Calculate from dates
    const baseAmount = bookingForm.baseRate * totalDays;
    const driverFee = bookingForm.withDriver ? 5000 * totalDays : 0;
    const insuranceFee = bookingForm.insurance ? 2000 * totalDays : 0;
    const subtotal = baseAmount + driverFee + insuranceFee;
    const discount = subtotal * 0.1; // 10% discount
    const vat = (subtotal - discount) * 0.075; // 7.5% VAT
    const total = subtotal - discount + vat;

    return (
      <div>
        <h3 style={{ fontSize: '18px', fontWeight: '700', color: colors.darkGrey, marginBottom: '8px' }}>
          Step 3: Add-ons & Confirmation
        </h3>
        <p style={{ fontSize: '14px', color: colors.mediumGrey, marginBottom: '24px' }}>
          Review booking details and add optional services
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
          {/* Left: Add-ons */}
          <div>
            <div style={{
              padding: '20px',
              backgroundColor: colors.white,
              border: `1px solid ${colors.lightGrey}`,
              borderRadius: '8px',
              marginBottom: '16px',
            }}>
              <h4 style={{ fontSize: '16px', fontWeight: '700', color: colors.darkGrey, marginBottom: '16px' }}>
                Optional Services
              </h4>

              <label style={{
                display: 'flex',
                alignItems: 'center',
                padding: '16px',
                backgroundColor: bookingForm.withDriver ? '#E8F4F8' : '#F8F9FA',
                border: `2px solid ${bookingForm.withDriver ? colors.info : colors.lightGrey}`,
                borderRadius: '8px',
                cursor: 'pointer',
                marginBottom: '12px',
                transition: 'all 0.2s',
              }}>
                <input
                  type="checkbox"
                  checked={bookingForm.withDriver}
                  onChange={(e) => setBookingForm({ ...bookingForm, withDriver: e.target.checked })}
                  style={{ marginRight: '12px', width: '18px', height: '18px', cursor: 'pointer' }}
                />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '14px', fontWeight: '600', color: colors.darkGrey }}>
                    Professional Driver Service
                  </div>
                  <div style={{ fontSize: '12px', color: colors.mediumGrey, marginTop: '4px' }}>
                    Experienced driver included for the duration
                  </div>
                </div>
                <div style={{ fontSize: '16px', fontWeight: '700', color: colors.darkGrey }}>
                  +₦5,000/day
                </div>
              </label>

              <label style={{
                display: 'flex',
                alignItems: 'center',
                padding: '16px',
                backgroundColor: bookingForm.insurance ? '#E8F4F8' : '#F8F9FA',
                border: `2px solid ${bookingForm.insurance ? colors.info : colors.lightGrey}`,
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}>
                <input
                  type="checkbox"
                  checked={bookingForm.insurance}
                  onChange={(e) => setBookingForm({ ...bookingForm, insurance: e.target.checked })}
                  style={{ marginRight: '12px', width: '18px', height: '18px', cursor: 'pointer' }}
                />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '14px', fontWeight: '600', color: colors.darkGrey }}>
                    Comprehensive Insurance
                  </div>
                  <div style={{ fontSize: '12px', color: colors.mediumGrey, marginTop: '4px' }}>
                    Full coverage for damage and theft
                  </div>
                </div>
                <div style={{ fontSize: '16px', fontWeight: '700', color: colors.darkGrey }}>
                  +₦2,000/day
                </div>
              </label>
            </div>

            <div style={{
              padding: '20px',
              backgroundColor: colors.white,
              border: `1px solid ${colors.lightGrey}`,
              borderRadius: '8px',
            }}>
              <h4 style={{ fontSize: '16px', fontWeight: '700', color: colors.darkGrey, marginBottom: '12px' }}>
                Additional Notes
              </h4>
              <textarea
                placeholder="Add any special requirements or notes..."
                value={bookingForm.notes}
                onChange={(e) => setBookingForm({ ...bookingForm, notes: e.target.value })}
                style={{
                  width: '100%',
                  padding: '12px',
                  border: `1px solid ${colors.lightGrey}`,
                  borderRadius: '6px',
                  fontSize: '14px',
                  minHeight: '100px',
                  fontFamily: 'inherit',
                  resize: 'vertical',
                }}
              />
            </div>
          </div>

          {/* Right: Summary */}
          <div>
            <div style={{
              padding: '20px',
              backgroundColor: colors.white,
              border: `2px solid ${colors.primary}`,
              borderRadius: '8px',
              position: 'sticky',
              top: '100px',
            }}>
              <h4 style={{ fontSize: '16px', fontWeight: '700', color: colors.darkGrey, marginBottom: '16px' }}>
                Booking Summary
              </h4>

              <div style={{ marginBottom: '16px', paddingBottom: '16px', borderBottom: `1px solid ${colors.lightGrey}` }}>
                <div style={{ fontSize: '12px', color: colors.mediumGrey, marginBottom: '4px' }}>Customer</div>
                <div style={{ fontSize: '14px', fontWeight: '600', color: colors.darkGrey }}>
                  {bookingForm.customer?.name || 'Not selected'}
                </div>
              </div>

              <div style={{ marginBottom: '16px', paddingBottom: '16px', borderBottom: `1px solid ${colors.lightGrey}` }}>
                <div style={{ fontSize: '12px', color: colors.mediumGrey, marginBottom: '4px' }}>Vehicle Type</div>
                <div style={{ fontSize: '14px', fontWeight: '600', color: colors.darkGrey }}>
                  {bookingForm.vehicleType || 'Not selected'}
                </div>
                <div style={{ fontSize: '12px', color: colors.mediumGrey, marginTop: '4px' }}>
                  ₦{bookingForm.baseRate.toLocaleString()}/day
                </div>
              </div>

              <div style={{ marginBottom: '16px', paddingBottom: '16px', borderBottom: `1px solid ${colors.lightGrey}` }}>
                <div style={{ fontSize: '12px', color: colors.mediumGrey, marginBottom: '4px' }}>Duration</div>
                <div style={{ fontSize: '14px', fontWeight: '600', color: colors.darkGrey }}>
                  {totalDays} days
                </div>
                <div style={{ fontSize: '12px', color: colors.mediumGrey, marginTop: '4px' }}>
                  {bookingForm.startDate} to {bookingForm.endDate}
                </div>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontSize: '13px', color: colors.darkGrey }}>Base Rental ({totalDays} days)</span>
                  <span style={{ fontSize: '13px', fontWeight: '600', color: colors.darkGrey }}>
                    ₦{baseAmount.toLocaleString()}
                  </span>
                </div>
                {bookingForm.withDriver && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span style={{ fontSize: '13px', color: colors.darkGrey }}>Driver Service</span>
                    <span style={{ fontSize: '13px', fontWeight: '600', color: colors.darkGrey }}>
                      ₦{driverFee.toLocaleString()}
                    </span>
                  </div>
                )}
                {bookingForm.insurance && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span style={{ fontSize: '13px', color: colors.darkGrey }}>Insurance</span>
                    <span style={{ fontSize: '13px', fontWeight: '600', color: colors.darkGrey }}>
                      ₦{insuranceFee.toLocaleString()}
                    </span>
                  </div>
                )}
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontSize: '13px', color: colors.success }}>Discount (10%)</span>
                  <span style={{ fontSize: '13px', fontWeight: '600', color: colors.success }}>
                    -₦{discount.toLocaleString()}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px', paddingBottom: '12px', borderBottom: `1px solid ${colors.lightGrey}` }}>
                  <span style={{ fontSize: '13px', color: colors.darkGrey }}>VAT (7.5%)</span>
                  <span style={{ fontSize: '13px', fontWeight: '600', color: colors.darkGrey }}>
                    ₦{vat.toLocaleString()}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '12px' }}>
                  <span style={{ fontSize: '16px', fontWeight: '700', color: colors.darkGrey }}>Total Amount</span>
                  <span style={{ fontSize: '20px', fontWeight: '700', color: colors.primary }}>
                    ₦{total.toLocaleString()}
                  </span>
                </div>
              </div>

              <Button
                icon={CheckCircle}
                size="large"
                onClick={() => {
                  setShowModal(true);
                  setModalType('success');
                }}
                style={{ width: '100%', justifyContent: 'center', marginTop: '16px' }}
              >
                Confirm Booking
              </Button>
            </div>
          </div>
        </div>

        <div style={{ marginTop: '24px', display: 'flex', gap: '12px' }}>
          <Button variant="secondary" icon={ChevronLeft} onClick={() => setNewBookingStep(2)}>
            Back
          </Button>
        </div>
      </div>
    );
  };

  // NEW BOOKING VIEW
  const NewBookingView = () => (
    <div style={{ padding: '32px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h2 style={{ fontSize: '24px', fontWeight: '700', color: colors.darkGrey, margin: 0 }}>
            Create New Booking
          </h2>
          <p style={{ fontSize: '14px', color: colors.mediumGrey, margin: '8px 0 0 0' }}>
            Follow the steps to create a new vehicle reservation
          </p>
        </div>
        <Button
          variant="ghost"
          icon={X}
          onClick={() => setBookingsSubView('list')}
        >
          Cancel
        </Button>
      </div>

      {/* Progress Steps */}
      <div style={{ marginBottom: '32px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'relative' }}>
          {/* Progress Line */}
          <div style={{
            position: 'absolute',
            top: '20px',
            left: '5%',
            right: '5%',
            height: '2px',
            backgroundColor: colors.lightGrey,
            zIndex: 0,
          }}>
            <div style={{
              height: '100%',
              backgroundColor: colors.primary,
              width: `${((newBookingStep - 1) / 2) * 100}%`,
              transition: 'width 0.3s',
            }} />
          </div>

          {/* Steps */}
          {[
            { num: 1, title: 'Customer', icon: User },
            { num: 2, title: 'Vehicle & Dates', icon: Car },
            { num: 3, title: 'Confirm', icon: CheckCircle },
          ].map(step => (
            <div key={step.num} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', position: 'relative', zIndex: 1 }}>
              <div style={{
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                backgroundColor: newBookingStep >= step.num ? colors.primary : colors.white,
                border: `3px solid ${newBookingStep >= step.num ? colors.primary : colors.lightGrey}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '8px',
                transition: 'all 0.3s',
              }}>
                <step.icon size={20} color={newBookingStep >= step.num ? colors.white : colors.mediumGrey} />
              </div>
              <div style={{
                fontSize: '13px',
                fontWeight: newBookingStep === step.num ? '700' : '500',
                color: newBookingStep >= step.num ? colors.primary : colors.mediumGrey,
                textAlign: 'center',
              }}>
                {step.title}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Step Content */}
      <div style={{
        backgroundColor: colors.white,
        padding: '32px',
        borderRadius: '12px',
        border: `1px solid ${colors.lightGrey}`,
        boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
      }}>
        {newBookingStep === 1 && <NewBookingStep1 />}
        {newBookingStep === 2 && <NewBookingStep2 />}
        {newBookingStep === 3 && <NewBookingStep3 />}
      </div>
    </div>
  );

  // BOOKING DETAILS VIEW
  const BookingDetailsView = () => {
    if (!selectedBooking) return null;

    return (
      <div style={{ padding: '32px', maxWidth: '1200px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '32px' }}>
          <div>
            <Button
              variant="ghost"
              icon={ChevronLeft}
              onClick={() => setBookingsSubView('list')}
              style={{ marginBottom: '12px' }}
            >
              Back to List
            </Button>
            <h2 style={{ fontSize: '28px', fontWeight: '700', color: colors.darkGrey, margin: '0 0 8px 0' }}>
              Booking {selectedBooking.id}
            </h2>
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
              <StatusBadge status={selectedBooking.status} />
              <PaymentBadge status={selectedBooking.paymentStatus} />
              <span style={{ fontSize: '13px', color: colors.mediumGrey }}>
                Created: Jan 12, 2026 at 10:30 AM
              </span>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '12px' }}>
            <Button variant="ghost" icon={Printer}>Print</Button>
            <Button variant="ghost" icon={Send}>Send Invoice</Button>
            <Button variant="ghost" icon={Edit}>Edit Booking</Button>
          </div>
        </div>

        {/* Main Content Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
          {/* Left Column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* Customer Info */}
            <div style={{
              backgroundColor: colors.white,
              padding: '24px',
              borderRadius: '12px',
              border: `1px solid ${colors.lightGrey}`,
            }}>
              <h3 style={{ fontSize: '18px', fontWeight: '700', color: colors.darkGrey, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Users size={20} color={colors.primary} />
                Customer Information
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
                <div>
                  <div style={{ fontSize: '12px', color: colors.mediumGrey, marginBottom: '4px' }}>Company Name</div>
                  <div style={{ fontSize: '15px', fontWeight: '600', color: colors.darkGrey }}>
                    {selectedBooking.customer.name}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: colors.mediumGrey, marginBottom: '4px' }}>Contact Person</div>
                  <div style={{ fontSize: '15px', fontWeight: '600', color: colors.darkGrey }}>
                    {selectedBooking.customer.contact}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: colors.mediumGrey, marginBottom: '4px' }}>Phone</div>
                  <div style={{ fontSize: '15px', fontWeight: '600', color: colors.darkGrey }}>
                    {selectedBooking.customer.phone}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: colors.mediumGrey, marginBottom: '4px' }}>Email</div>
                  <div style={{ fontSize: '15px', fontWeight: '600', color: colors.darkGrey }}>
                    {selectedBooking.customer.email}
                  </div>
                </div>
              </div>
            </div>

            {/* Vehicle & Trip Details */}
            <div style={{
              backgroundColor: colors.white,
              padding: '24px',
              borderRadius: '12px',
              border: `1px solid ${colors.lightGrey}`,
            }}>
              <h3 style={{ fontSize: '18px', fontWeight: '700', color: colors.darkGrey, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Car size={20} color={colors.primary} />
                Vehicle & Trip Details
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
                <div>
                  <div style={{ fontSize: '12px', color: colors.mediumGrey, marginBottom: '4px' }}>Vehicle</div>
                  <div style={{ fontSize: '15px', fontWeight: '600', color: colors.darkGrey }}>
                    {selectedBooking.vehicle.name}
                  </div>
                  <div style={{ fontSize: '13px', color: colors.mediumGrey, marginTop: '2px' }}>
                    {selectedBooking.vehicle.id} • {selectedBooking.vehicle.type}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: colors.mediumGrey, marginBottom: '4px' }}>Driver</div>
                  <div style={{ fontSize: '15px', fontWeight: '600', color: colors.darkGrey }}>
                    {selectedBooking.withDriver ? selectedBooking.driver : 'Self-Drive'}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: colors.mediumGrey, marginBottom: '4px' }}>Pickup Date</div>
                  <div style={{ fontSize: '15px', fontWeight: '600', color: colors.darkGrey }}>
                    {selectedBooking.startDate}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: colors.mediumGrey, marginBottom: '4px' }}>Return Date</div>
                  <div style={{ fontSize: '15px', fontWeight: '600', color: colors.darkGrey }}>
                    {selectedBooking.endDate}
                  </div>
                </div>
                <div style={{ gridColumn: 'span 2' }}>
                  <div style={{ fontSize: '12px', color: colors.mediumGrey, marginBottom: '4px' }}>Duration</div>
                  <div style={{ fontSize: '15px', fontWeight: '600', color: colors.darkGrey }}>
                    {selectedBooking.days} days
                  </div>
                </div>
              </div>
            </div>

            {/* Timeline */}
            <div style={{
              backgroundColor: colors.white,
              padding: '24px',
              borderRadius: '12px',
              border: `1px solid ${colors.lightGrey}`,
            }}>
              <h3 style={{ fontSize: '18px', fontWeight: '700', color: colors.darkGrey, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Clock size={20} color={colors.primary} />
                Booking Timeline
              </h3>
              <div style={{ position: 'relative', paddingLeft: '32px' }}>
                {/* Timeline line */}
                <div style={{
                  position: 'absolute',
                  left: '8px',
                  top: '8px',
                  bottom: '8px',
                  width: '2px',
                  backgroundColor: colors.lightGrey,
                }} />

                {/* Timeline items */}
                {[
                  { status: 'completed', title: 'Booking Created', time: 'Jan 12, 2026 - 10:30 AM', icon: Check },
                  { status: 'completed', title: 'Payment Received', time: 'Jan 12, 2026 - 10:35 AM', icon: DollarSign },
                  { status: 'completed', title: 'Booking Confirmed', time: 'Jan 12, 2026 - 10:36 AM', icon: CheckCircle },
                  { status: 'active', title: 'Driver Assigned', time: 'Jan 13, 2026 - 09:15 AM', icon: User },
                  { status: 'pending', title: 'Vehicle Handover', time: 'Scheduled: Jan 15, 2026', icon: Car },
                ].map((item, idx) => (
                  <div key={idx} style={{ display: 'flex', gap: '16px', marginBottom: '20px', position: 'relative' }}>
                    <div style={{
                      position: 'absolute',
                      left: '-24px',
                      width: '16px',
                      height: '16px',
                      borderRadius: '50%',
                      backgroundColor: item.status === 'completed' ? colors.success : item.status === 'active' ? colors.info : colors.lightGrey,
                      border: `2px solid ${colors.white}`,
                    }} />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '14px', fontWeight: '600', color: colors.darkGrey }}>
                        {item.title}
                      </div>
                      <div style={{ fontSize: '12px', color: colors.mediumGrey, marginTop: '2px' }}>
                        {item.time}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column - Financial Summary */}
          <div>
            <div style={{
              backgroundColor: colors.white,
              padding: '24px',
              borderRadius: '12px',
              border: `2px solid ${colors.primary}`,
              position: 'sticky',
              top: '100px',
            }}>
              <h3 style={{ fontSize: '18px', fontWeight: '700', color: colors.darkGrey, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FileText size={20} color={colors.primary} />
                Financial Summary
              </h3>

              <div style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <span style={{ fontSize: '13px', color: colors.darkGrey }}>Base Rental (5 days)</span>
                  <span style={{ fontSize: '13px', fontWeight: '600', color: colors.darkGrey }}>₦125,000</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <span style={{ fontSize: '13px', color: colors.darkGrey }}>Driver Service</span>
                  <span style={{ fontSize: '13px', fontWeight: '600', color: colors.darkGrey }}>₦15,000</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <span style={{ fontSize: '13px', color: colors.darkGrey }}>Insurance</span>
                  <span style={{ fontSize: '13px', fontWeight: '600', color: colors.darkGrey }}>₦10,000</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <span style={{ fontSize: '13px', color: colors.success }}>Discount (10%)</span>
                  <span style={{ fontSize: '13px', fontWeight: '600', color: colors.success }}>-₦12,500</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px', paddingBottom: '16px', borderBottom: `1px solid ${colors.lightGrey}` }}>
                  <span style={{ fontSize: '13px', color: colors.darkGrey }}>VAT (7.5%)</span>
                  <span style={{ fontSize: '13px', fontWeight: '600', color: colors.darkGrey }}>₦10,313</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
                  <span style={{ fontSize: '16px', fontWeight: '700', color: colors.darkGrey }}>Total Amount</span>
                  <span style={{ fontSize: '24px', fontWeight: '700', color: colors.primary }}>₦147,813</span>
                </div>

                <div style={{
                  padding: '12px',
                  backgroundColor: '#D4EDDA',
                  borderRadius: '6px',
                  marginBottom: '16px',
                }}>
                  <div style={{ fontSize: '12px', color: '#155724', fontWeight: '600', marginBottom: '4px' }}>
                    Payment Status: PAID
                  </div>
                  <div style={{ fontSize: '11px', color: '#155724' }}>
                    Paid on Jan 12, 2026 via Bank Transfer
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <Button icon={Printer} size="medium" style={{ width: '100%', justifyContent: 'center' }}>
                  Print Invoice
                </Button>
                <Button variant="secondary" icon={Download} size="medium" style={{ width: '100%', justifyContent: 'center' }}>
                  Download PDF
                </Button>
                <Button variant="secondary" icon={Send} size="medium" style={{ width: '100%', justifyContent: 'center' }}>
                  Email to Customer
                </Button>
              </div>

              {/* Quick Actions */}
              <div style={{ marginTop: '20px', paddingTop: '20px', borderTop: `1px solid ${colors.lightGrey}` }}>
                <div style={{ fontSize: '14px', fontWeight: '600', color: colors.darkGrey, marginBottom: '12px' }}>
                  Quick Actions
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <Button variant="ghost" icon={Edit} size="small" style={{ width: '100%', justifyContent: 'flex-start' }}>
                    Modify Booking
                  </Button>
                  <Button variant="ghost" icon={RefreshCw} size="small" style={{ width: '100%', justifyContent: 'flex-start' }}>
                    Extend Rental
                  </Button>
                  <Button variant="ghost" icon={MessageSquare} size="small" style={{ width: '100%', justifyContent: 'flex-start' }}>
                    Contact Customer
                  </Button>
                  <Button variant="ghost" icon={X} size="small" style={{ width: '100%', justifyContent: 'flex-start', color: colors.danger }}>
                    Cancel Booking
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Calendar View (Placeholder)
  const CalendarView = () => (
    <div style={{ padding: '32px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: '700', color: colors.darkGrey, margin: 0 }}>
          Booking Calendar
        </h2>
        <Button variant="secondary" icon={Calendar} onClick={() => setBookingsSubView('list')}>
          List View
        </Button>
      </div>
      <div style={{
        backgroundColor: colors.white,
        padding: '80px',
        borderRadius: '12px',
        border: `1px solid ${colors.lightGrey}`,
        textAlign: 'center',
      }}>
        <CalendarDays size={64} color={colors.mediumGrey} style={{ margin: '0 auto 20px' }} />
        <h3 style={{ color: colors.darkGrey, margin: '0 0 12px 0' }}>Calendar View</h3>
        <p style={{ color: colors.mediumGrey }}>Interactive calendar with booking visualization coming soon</p>
      </div>
    </div>
  );

  // Success Modal
  const SuccessModal = () => (
    <Modal isOpen={showModal && modalType === 'success'} onClose={() => setShowModal(false)} title="Booking Created Successfully!" width="500px">
      <div style={{ textAlign: 'center', padding: '20px 0' }}>
        <div style={{
          width: '80px',
          height: '80px',
          borderRadius: '50%',
          backgroundColor: `${colors.success}20`,
          margin: '0 auto 20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <CheckCircle size={48} color={colors.success} />
        </div>
        <h3 style={{ fontSize: '20px', fontWeight: '700', color: colors.darkGrey, marginBottom: '12px' }}>
          Booking Confirmed!
        </h3>
        <p style={{ fontSize: '14px', color: colors.mediumGrey, marginBottom: '24px' }}>
          Booking ID: <strong style={{ color: colors.primary }}>BK-2402</strong> has been created successfully.
        </p>
        <div style={{ backgroundColor: '#F8F9FA', padding: '16px', borderRadius: '8px', marginBottom: '24px' }}>
          <div style={{ fontSize: '13px', color: colors.mediumGrey, marginBottom: '8px' }}>
            Next Steps:
          </div>
          <div style={{ fontSize: '14px', color: colors.darkGrey, textAlign: 'left' }}>
            ✓ Invoice sent to customer<br />
            ✓ Payment confirmation pending<br />
            ✓ Driver will be assigned once payment is received
          </div>
        </div>
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
          <Button
            variant="secondary"
            onClick={() => {
              setShowModal(false);
              setBookingsSubView('list');
            }}
          >
            View All Bookings
          </Button>
          <Button
            onClick={() => {
              setShowModal(false);
              setBookingsSubView('new');
              setNewBookingStep(1);
            }}
          >
            Create Another
          </Button>
        </div>
      </div>
    </Modal>
  );

  // Main render
  return (
    <div style={{
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif",
      backgroundColor: '#F5F7FA',
      minHeight: '100vh',
    }}>
      <Sidebar />
      <div style={{
        marginLeft: sidebarOpen ? '280px' : '0',
        transition: 'margin-left 0.3s ease',
      }}>
        <Header />
        <div style={{ marginTop: '70px', minHeight: 'calc(100vh - 70px)' }}>
          {currentView === 'bookings' && (
            <>
              {bookingsSubView === 'list' && <BookingsListView />}
              {bookingsSubView === 'new' && <NewBookingView />}
              {bookingsSubView === 'details' && <BookingDetailsView />}
              {bookingsSubView === 'calendar' && <CalendarView />}
            </>
          )}
          {currentView !== 'bookings' && (
            <div style={{ padding: '80px 32px', textAlign: 'center' }}>
              <div style={{
                display: 'inline-block',
                padding: '40px 60px',
                backgroundColor: colors.white,
                borderRadius: '12px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
              }}>
                <div style={{
                  width: '80px',
                  height: '80px',
                  backgroundColor: `${colors.primary}15`,
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 20px',
                }}>
                  {navItems.find(item => item.id === currentView)?.icon &&
                    React.createElement(navItems.find(item => item.id === currentView).icon, {
                      size: 40,
                      color: colors.primary,
                    })
                  }
                </div>
                <h2 style={{ color: colors.darkGrey, margin: '0 0 12px 0', fontSize: '24px', fontWeight: '700' }}>
                  {navItems.find(item => item.id === currentView)?.label}
                </h2>
                <p style={{ color: colors.mediumGrey, margin: 0, fontSize: '15px' }}>
                  This module is currently under development
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
      {/* Modals */}
      <SuccessModal />
    </div>
  );
};

export default CNIFleetManagementUI;
