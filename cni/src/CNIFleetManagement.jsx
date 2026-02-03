import React, { useState, useEffect } from 'react';
import { Car, Calendar, Users, Wrench, DollarSign, BarChart3, Settings, Menu, Bell, Search, MapPin,
         ChevronRight, CheckCircle, AlertTriangle, XCircle, Plus, Filter, Download, Upload, Edit,
         Trash2, Eye, X, Clock, Phone, Mail, User, CreditCard, FileText, Camera, CheckSquare,
         AlertCircle, RefreshCw, Send, Printer, MessageSquare, CalendarDays, ChevronLeft, Check,
         Fuel, Navigation, Shield, Activity, Battery, Gauge, FileCheck, AlertOctagon,
         MoreVertical, Zap, Circle, Map, Truck } from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default marker icons in Leaflet with webpack/vite
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Custom vehicle marker icons based on status
const createVehicleIcon = (status, isMoving) => {
  const colors = {
    active: '#28A745',
    available: '#6C757D',
    booked: '#007BFF',
    maintenance: '#FFC107',
    dormant: '#DC3545',
  };
  const color = colors[status] || colors.available;

  return L.divIcon({
    className: 'custom-vehicle-marker',
    html: `
      <div style="
        width: 36px;
        height: 36px;
        background-color: ${color};
        border: 3px solid white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        ${isMoving ? 'animation: pulse 1.5s infinite;' : ''}
      ">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="white" stroke="white" stroke-width="1">
          <path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9L18 10l-2-4H8L6 10l-2.5 1.1C2.7 11.3 2 12.1 2 13v3c0 .6.4 1 1 1h2"/>
          <circle cx="7" cy="17" r="2"/>
          <circle cx="17" cy="17" r="2"/>
        </svg>
      </div>
    `,
    iconSize: [36, 36],
    iconAnchor: [18, 18],
    popupAnchor: [0, -18],
  });
};

const CNIFleetManagementUI = () => {
  const [currentView, setCurrentView] = useState('showcase');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [bookingsSubView, setBookingsSubView] = useState('list'); // list, new, details, calendar
  const [selectedBooking, setSelectedBooking] = useState(null);
  const [newBookingStep, setNewBookingStep] = useState(1);
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState(null);
  const [filterStatus, setFilterStatus] = useState('all');

  // Fleet Management state
  const [fleetSubView, setFleetSubView] = useState('list'); // list, details, map
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [fleetStatusFilter, setFleetStatusFilter] = useState('all');
  const [fleetViewMode, setFleetViewMode] = useState('grid'); // grid, table
  const [showAddVehicleModal, setShowAddVehicleModal] = useState(false);
  const [newVehicleForm, setNewVehicleForm] = useState({
    name: '',
    type: 'Sedan',
    make: '',
    model: '',
    year: new Date().getFullYear(),
    registrationNo: '',
    color: '',
    fuelType: 'Petrol',
    transmission: 'Automatic',
    seats: 5,
  });

  // Showcase/Client Booking state
  const [showcaseView, setShowcaseView] = useState('browse'); // browse, vehicle, form, confirmation
  const [selectedShowcaseVehicle, setSelectedShowcaseVehicle] = useState(null);
  const [showcaseFilter, setShowcaseFilter] = useState({ type: 'all', priceRange: 'all' });
  const [clientBooking, setClientBooking] = useState({
    pickupDate: '',
    returnDate: '',
    withDriver: true,
    withInsurance: true,
    withFuel: true,
    withGPS: false,
    customerName: '',
    customerEmail: '',
    customerPhone: '',
    customerCompany: '',
    pickupLocation: '',
    returnLocation: '',
    pickupTime: '09:00',
    returnTime: '09:00',
    notes: '',
  });
  const [bookingReference, setBookingReference] = useState('');

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

  // Fleet Management Data - Complete Vehicle Database
  const fleetVehicles = [
    {
      id: 'LA-001',
      name: 'Toyota Camry 2023',
      type: 'Sedan',
      make: 'Toyota',
      model: 'Camry',
      year: 2023,
      vin: 'JTDKN3DU5A0123456',
      registrationNo: 'LA-001-ABC',
      status: 'active', // available, booked, active, maintenance, workshop, dormant
      fuelType: 'Petrol',
      transmission: 'Automatic',
      seats: 5,
      color: 'White',
      purchaseDate: '2023-03-15',
      purchaseCost: 28000000,
      currentValuation: 24500000,
      mileage: 45230,
      lastServiceMileage: 40000,
      nextServiceDue: 50000,
      fuelLevel: 75,
      batteryVoltage: 12.8,
      insuranceExpiry: '2026-03-15',
      registrationExpiry: '2026-06-20',
      assignedDriver: 'John Obi',
      currentBooking: 'BK-2401',
      currentClient: 'Acme Corporation',
      gps: {
        latitude: 6.4281,
        longitude: 3.4219,
        address: 'Victoria Island, Lagos',
        speed: 45,
        heading: 'NE',
        ignition: true,
        lastUpdate: '2026-02-03T10:30:00',
        signalQuality: 'Good'
      },
      documents: [
        { type: 'Vehicle License', expiry: '2026-06-20', status: 'valid' },
        { type: 'Insurance', expiry: '2026-03-15', status: 'valid' },
        { type: 'Road Worthiness', expiry: '2026-08-10', status: 'valid' },
        { type: 'Hackney Permit', expiry: '2026-04-01', status: 'expiring' },
      ],
      maintenanceHistory: [
        { date: '2025-12-10', type: 'Routine Service', cost: 85000, vendor: 'Toyota Nigeria', mileage: 40000 },
        { date: '2025-09-05', type: 'Tire Replacement', cost: 320000, vendor: 'Dunlop Nigeria', mileage: 35000 },
      ]
    },
    {
      id: 'LA-002',
      name: 'Honda Accord 2022',
      type: 'Sedan',
      make: 'Honda',
      model: 'Accord',
      year: 2022,
      vin: 'JHMCG5650CC123789',
      registrationNo: 'LA-002-DEF',
      status: 'available',
      fuelType: 'Petrol',
      transmission: 'Automatic',
      seats: 5,
      color: 'Silver',
      purchaseDate: '2022-08-20',
      purchaseCost: 22000000,
      currentValuation: 18500000,
      mileage: 62150,
      lastServiceMileage: 60000,
      nextServiceDue: 65000,
      fuelLevel: 40,
      batteryVoltage: 12.6,
      insuranceExpiry: '2026-08-20',
      registrationExpiry: '2026-09-15',
      assignedDriver: null,
      currentBooking: null,
      currentClient: null,
      gps: {
        latitude: 6.4478,
        longitude: 3.4723,
        address: 'Lekki Phase 1, Lagos',
        speed: 0,
        heading: '-',
        ignition: false,
        lastUpdate: '2026-02-03T08:15:00',
        signalQuality: 'Good'
      },
      documents: [
        { type: 'Vehicle License', expiry: '2026-09-15', status: 'valid' },
        { type: 'Insurance', expiry: '2026-08-20', status: 'valid' },
        { type: 'Road Worthiness', expiry: '2026-10-05', status: 'valid' },
        { type: 'Hackney Permit', expiry: '2026-07-12', status: 'valid' },
      ],
      maintenanceHistory: [
        { date: '2026-01-15', type: 'Routine Service', cost: 75000, vendor: 'Honda Nigeria', mileage: 60000 },
      ]
    },
    {
      id: 'LA-003',
      name: 'Lexus RX350 2024',
      type: 'SUV',
      make: 'Lexus',
      model: 'RX350',
      year: 2024,
      vin: '2T2BZMCA5KC654321',
      registrationNo: 'LA-003-GHI',
      status: 'booked',
      fuelType: 'Petrol',
      transmission: 'Automatic',
      seats: 5,
      color: 'Black',
      purchaseDate: '2024-01-10',
      purchaseCost: 65000000,
      currentValuation: 58000000,
      mileage: 18500,
      lastServiceMileage: 15000,
      nextServiceDue: 20000,
      fuelLevel: 90,
      batteryVoltage: 12.9,
      insuranceExpiry: '2027-01-10',
      registrationExpiry: '2027-02-15',
      assignedDriver: 'Ada Eze',
      currentBooking: 'BK-2399',
      currentClient: 'TechCo Nigeria',
      gps: {
        latitude: 6.5833,
        longitude: 3.3500,
        address: 'Ikeja GRA, Lagos',
        speed: 0,
        heading: '-',
        ignition: false,
        lastUpdate: '2026-02-03T09:45:00',
        signalQuality: 'Good'
      },
      documents: [
        { type: 'Vehicle License', expiry: '2027-02-15', status: 'valid' },
        { type: 'Insurance', expiry: '2027-01-10', status: 'valid' },
        { type: 'Road Worthiness', expiry: '2027-03-20', status: 'valid' },
        { type: 'Hackney Permit', expiry: '2027-01-25', status: 'valid' },
      ],
      maintenanceHistory: []
    },
    {
      id: 'LA-004',
      name: 'Toyota Hilux 2023',
      type: 'Truck',
      make: 'Toyota',
      model: 'Hilux',
      year: 2023,
      vin: 'AHTFZ29G509876543',
      registrationNo: 'LA-004-JKL',
      status: 'active',
      fuelType: 'Diesel',
      transmission: 'Automatic',
      seats: 5,
      color: 'Grey',
      purchaseDate: '2023-06-01',
      purchaseCost: 42000000,
      currentValuation: 38000000,
      mileage: 52800,
      lastServiceMileage: 50000,
      nextServiceDue: 55000,
      fuelLevel: 60,
      batteryVoltage: 12.7,
      insuranceExpiry: '2026-06-01',
      registrationExpiry: '2026-07-10',
      assignedDriver: 'Chidi Okoro',
      currentBooking: 'BK-2398',
      currentClient: 'BuildCo Ltd',
      gps: {
        latitude: 6.6318,
        longitude: 3.3515,
        address: 'Ojodu Berger, Lagos',
        speed: 62,
        heading: 'N',
        ignition: true,
        lastUpdate: '2026-02-03T10:28:00',
        signalQuality: 'Good'
      },
      documents: [
        { type: 'Vehicle License', expiry: '2026-07-10', status: 'valid' },
        { type: 'Insurance', expiry: '2026-06-01', status: 'expiring' },
        { type: 'Road Worthiness', expiry: '2026-05-15', status: 'expiring' },
        { type: 'Hackney Permit', expiry: '2026-08-20', status: 'valid' },
      ],
      maintenanceHistory: [
        { date: '2025-11-20', type: 'Routine Service', cost: 95000, vendor: 'Toyota Nigeria', mileage: 50000 },
        { date: '2025-08-10', type: 'Brake Pads', cost: 180000, vendor: 'AutoFix Lagos', mileage: 45000 },
      ]
    },
    {
      id: 'LA-005',
      name: 'Mercedes C-Class 2024',
      type: 'Sedan',
      make: 'Mercedes-Benz',
      model: 'C-Class',
      year: 2024,
      vin: 'WDDWF4KB1KR111222',
      registrationNo: 'LA-005-MNO',
      status: 'maintenance',
      fuelType: 'Petrol',
      transmission: 'Automatic',
      seats: 5,
      color: 'Black',
      purchaseDate: '2024-02-28',
      purchaseCost: 55000000,
      currentValuation: 50000000,
      mileage: 12300,
      lastServiceMileage: 10000,
      nextServiceDue: 15000,
      fuelLevel: 25,
      batteryVoltage: 12.4,
      insuranceExpiry: '2027-02-28',
      registrationExpiry: '2027-03-15',
      assignedDriver: null,
      currentBooking: null,
      currentClient: null,
      gps: {
        latitude: 6.4598,
        longitude: 3.5452,
        address: 'Ajah, Lagos',
        speed: 0,
        heading: '-',
        ignition: false,
        lastUpdate: '2026-02-02T16:00:00',
        signalQuality: 'Good'
      },
      documents: [
        { type: 'Vehicle License', expiry: '2027-03-15', status: 'valid' },
        { type: 'Insurance', expiry: '2027-02-28', status: 'valid' },
        { type: 'Road Worthiness', expiry: '2027-04-10', status: 'valid' },
        { type: 'Hackney Permit', expiry: '2027-02-15', status: 'valid' },
      ],
      maintenanceHistory: [
        { date: '2026-02-01', type: 'AC Repair', cost: 450000, vendor: 'Mercedes Nigeria', mileage: 12300, status: 'in-progress' },
      ]
    },
    {
      id: 'LA-006',
      name: 'Toyota Corolla 2022',
      type: 'Sedan',
      make: 'Toyota',
      model: 'Corolla',
      year: 2022,
      vin: 'JTDBR3EH0C0333444',
      registrationNo: 'LA-006-PQR',
      status: 'available',
      fuelType: 'Petrol',
      transmission: 'Automatic',
      seats: 5,
      color: 'Blue',
      purchaseDate: '2022-05-15',
      purchaseCost: 18000000,
      currentValuation: 14500000,
      mileage: 78500,
      lastServiceMileage: 75000,
      nextServiceDue: 80000,
      fuelLevel: 55,
      batteryVoltage: 12.5,
      insuranceExpiry: '2026-05-15',
      registrationExpiry: '2026-06-20',
      assignedDriver: null,
      currentBooking: null,
      currentClient: null,
      gps: {
        latitude: 6.4983,
        longitude: 3.3486,
        address: 'Surulere, Lagos',
        speed: 0,
        heading: '-',
        ignition: false,
        lastUpdate: '2026-02-03T07:30:00',
        signalQuality: 'Good'
      },
      documents: [
        { type: 'Vehicle License', expiry: '2026-06-20', status: 'valid' },
        { type: 'Insurance', expiry: '2026-05-15', status: 'expiring' },
        { type: 'Road Worthiness', expiry: '2026-07-01', status: 'valid' },
        { type: 'Hackney Permit', expiry: '2026-04-10', status: 'expiring' },
      ],
      maintenanceHistory: [
        { date: '2026-01-05', type: 'Routine Service', cost: 65000, vendor: 'Toyota Nigeria', mileage: 75000 },
      ]
    },
    {
      id: 'LA-007',
      name: 'Toyota Prado 2023',
      type: 'SUV',
      make: 'Toyota',
      model: 'Land Cruiser Prado',
      year: 2023,
      vin: 'JTEBR3EH0C0555666',
      registrationNo: 'LA-007-STU',
      status: 'dormant',
      fuelType: 'Diesel',
      transmission: 'Automatic',
      seats: 7,
      color: 'White',
      purchaseDate: '2023-09-01',
      purchaseCost: 72000000,
      currentValuation: 65000000,
      mileage: 8200,
      lastServiceMileage: 5000,
      nextServiceDue: 10000,
      fuelLevel: 10,
      batteryVoltage: 11.2,
      insuranceExpiry: '2026-09-01',
      registrationExpiry: '2026-10-15',
      assignedDriver: null,
      currentBooking: null,
      currentClient: null,
      gps: {
        latitude: 6.4412,
        longitude: 3.4089,
        address: 'Ikoyi, Lagos',
        speed: 0,
        heading: '-',
        ignition: false,
        lastUpdate: '2026-01-15T14:00:00',
        signalQuality: 'Weak'
      },
      documents: [
        { type: 'Vehicle License', expiry: '2026-10-15', status: 'valid' },
        { type: 'Insurance', expiry: '2026-09-01', status: 'valid' },
        { type: 'Road Worthiness', expiry: '2026-11-20', status: 'valid' },
        { type: 'Hackney Permit', expiry: '2026-08-05', status: 'valid' },
      ],
      maintenanceHistory: []
    },
    {
      id: 'LA-008',
      name: 'Toyota Hiace 2023',
      type: 'Bus',
      make: 'Toyota',
      model: 'Hiace',
      year: 2023,
      vin: 'JTFSK20P700777888',
      registrationNo: 'LA-008-VWX',
      status: 'active',
      fuelType: 'Diesel',
      transmission: 'Manual',
      seats: 14,
      color: 'White',
      purchaseDate: '2023-04-10',
      purchaseCost: 35000000,
      currentValuation: 31000000,
      mileage: 95600,
      lastServiceMileage: 90000,
      nextServiceDue: 100000,
      fuelLevel: 80,
      batteryVoltage: 12.8,
      insuranceExpiry: '2026-04-10',
      registrationExpiry: '2026-05-20',
      assignedDriver: 'Emeka Nwankwo',
      currentBooking: 'BK-2405',
      currentClient: 'Shell Nigeria',
      gps: {
        latitude: 6.4550,
        longitude: 3.3841,
        address: 'Lagos Island, Lagos',
        speed: 55,
        heading: 'E',
        ignition: true,
        lastUpdate: '2026-02-03T10:25:00',
        signalQuality: 'Good'
      },
      documents: [
        { type: 'Vehicle License', expiry: '2026-05-20', status: 'valid' },
        { type: 'Insurance', expiry: '2026-04-10', status: 'expiring' },
        { type: 'Road Worthiness', expiry: '2026-06-15', status: 'valid' },
        { type: 'Hackney Permit', expiry: '2026-03-25', status: 'expiring' },
      ],
      maintenanceHistory: [
        { date: '2025-12-20', type: 'Routine Service', cost: 120000, vendor: 'Toyota Nigeria', mileage: 90000 },
        { date: '2025-10-05', type: 'Clutch Replacement', cost: 280000, vendor: 'AutoFix Lagos', mileage: 85000 },
      ]
    },
  ];

  // Fleet statistics
  const fleetStats = {
    total: fleetVehicles.length,
    available: fleetVehicles.filter(v => v.status === 'available').length,
    booked: fleetVehicles.filter(v => v.status === 'booked').length,
    active: fleetVehicles.filter(v => v.status === 'active').length,
    maintenance: fleetVehicles.filter(v => v.status === 'maintenance').length,
    dormant: fleetVehicles.filter(v => v.status === 'dormant').length,
    expiringDocs: fleetVehicles.filter(v => v.documents.some(d => d.status === 'expiring')).length,
    lowFuel: fleetVehicles.filter(v => v.fuelLevel < 25).length,
  };

  // Filter fleet by status
  const filteredFleet = fleetStatusFilter === 'all'
    ? fleetVehicles
    : fleetVehicles.filter(v => v.status === fleetStatusFilter);

  // Showcase vehicles for client booking
  const showcaseVehicles = [
    { id: 'SV-001', name: 'Toyota Camry 2023', type: 'Sedan', seats: 5, rating: 4.8, dailyRate: 35000, image: 'https://pictures-nigeria.jijistatic.net/159042428_MzAwLTQwMC1jOWRjOWNmNThi.webp', available: true, features: ['AC', 'Bluetooth', 'USB Charging', 'Leather Seats'] },
    { id: 'SV-002', name: 'Honda Accord 2022', type: 'Sedan', seats: 5, rating: 4.7, dailyRate: 32000, image: 'https://pictures-nigeria.jijistatic.net/183129966_MzAwLTQwMC1jYzYzNTFiODY4.webp', available: true, features: ['AC', 'Bluetooth', 'Sunroof', 'Backup Camera'] },
    { id: 'SV-003', name: 'Mercedes E-Class 2024', type: 'Luxury', seats: 5, rating: 4.9, dailyRate: 85000, image: 'https://pictures-nigeria.jijistatic.net/164741821_MzAwLTI5Ni01MTYxZWIwZWIy.webp', available: true, features: ['AC', 'Premium Sound', 'Massage Seats', 'WiFi'] },
    { id: 'SV-004', name: 'BMW 5 Series 2024', type: 'Luxury', seats: 5, rating: 4.9, dailyRate: 90000, image: 'https://pictures-nigeria.jijistatic.net/168672548_MzAwLTQwMC1jZGZlMjYxODE2.webp', available: false, features: ['AC', 'Premium Sound', 'Heads-up Display', 'Adaptive Cruise'] },
    { id: 'SV-005', name: 'Toyota Prado 2023', type: 'SUV', seats: 7, rating: 4.8, dailyRate: 65000, image: 'https://pictures-nigeria.jijistatic.net/161934706_MzAwLTIyNS0zMGNjYTdiYzQ0.webp', available: true, features: ['AC', '4WD', 'Third Row Seating', 'Roof Rack'] },
    { id: 'SV-006', name: 'Lexus RX350 2024', type: 'SUV', seats: 5, rating: 4.9, dailyRate: 75000, image: 'https://pictures-nigeria.jijistatic.net/170881954_MzAwLTM1Ny0zMjFkZjBjY2Qy.webp', available: true, features: ['AC', 'Premium Sound', 'Panoramic Roof', 'Ventilated Seats'] },
    { id: 'SV-007', name: 'Toyota Hiace 2023', type: 'Bus', seats: 14, rating: 4.6, dailyRate: 55000, image: 'https://pictures-nigeria.jijistatic.net/175680214_MzAwLTUzMy0xYWFhNjNkMDAx.webp', available: true, features: ['AC', 'PA System', 'Luggage Space', 'Reclining Seats'] },
    { id: 'SV-008', name: 'Toyota Hilux 2023', type: 'Truck', seats: 5, rating: 4.7, dailyRate: 45000, image: 'https://pictures-nigeria.jijistatic.net/168676255_MzAwLTM1Ni02YjY3ZDE4YTAy.webp', available: true, features: ['AC', '4WD', 'Tow Package', 'Bed Liner'] },
    { id: 'SV-009', name: 'Toyota Corolla 2023', type: 'Sedan', seats: 5, rating: 4.6, dailyRate: 28000, image: 'https://pictures-nigeria.jijistatic.net/160873070_MzAwLTQwMC02NDQxNmQ3MGU0.webp', available: true, features: ['AC', 'Bluetooth', 'Fuel Efficient', 'Apple CarPlay'] },
    { id: 'SV-010', name: 'Range Rover Sport 2024', type: 'Luxury', seats: 5, rating: 5.0, dailyRate: 150000, image: 'https://pictures-nigeria.jijistatic.net/137162561_MzAwLTIyNS1iM2FmYzM2YWUw.webp', available: true, features: ['AC', 'Premium Everything', 'Terrain Response', 'Meridian Sound'] },
  ];

  // Filter showcase vehicles
  const filteredShowcaseVehicles = showcaseVehicles.filter(v => {
    if (showcaseFilter.type !== 'all' && v.type !== showcaseFilter.type) return false;
    if (showcaseFilter.priceRange === 'budget' && v.dailyRate > 40000) return false;
    if (showcaseFilter.priceRange === 'mid' && (v.dailyRate < 40000 || v.dailyRate > 70000)) return false;
    if (showcaseFilter.priceRange === 'premium' && v.dailyRate < 70000) return false;
    return true;
  });

  // Calculate booking total
  const calculateBookingTotal = () => {
    if (!selectedShowcaseVehicle || !clientBooking.pickupDate || !clientBooking.returnDate) return { days: 0, subtotal: 0, vat: 0, total: 0 };
    const start = new Date(clientBooking.pickupDate);
    const end = new Date(clientBooking.returnDate);
    const days = Math.max(1, Math.ceil((end - start) / (1000 * 60 * 60 * 24)));
    const baseAmount = selectedShowcaseVehicle.dailyRate * days;
    const driverFee = clientBooking.withDriver ? 5000 * days : 0;
    const insuranceFee = clientBooking.withInsurance ? 2500 * days : 0;
    const fuelFee = clientBooking.withFuel ? 15000 : 0;
    const gpsFee = clientBooking.withGPS ? 1000 * days : 0;
    const subtotal = baseAmount + driverFee + insuranceFee + fuelFee + gpsFee;
    const vat = subtotal * 0.075;
    return { days, baseAmount, driverFee, insuranceFee, fuelFee, gpsFee, subtotal, vat, total: subtotal + vat };
  };

  // Filter bookings by status
  const filteredBookings = filterStatus === 'all'
    ? allBookings
    : allBookings.filter(b => b.status === filterStatus);

  // Navigation items
  const navItems = [
    { id: 'showcase', label: 'Book a Vehicle', icon: Car, badge: null, highlight: true },
    // { id: 'dashboard', label: 'Dashboard', icon: BarChart3, badge: null },
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
              if (item.id === 'fleet') setFleetSubView('list');
              if (item.id === 'showcase') setShowcaseView('browse');
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

  // Vehicle Status Badge for Fleet
  const VehicleStatusBadge = ({ status }) => {
    const statusConfig = {
      available: { bg: '#D4EDDA', text: '#155724', label: 'Available', icon: CheckCircle },
      booked: { bg: '#D1ECF1', text: '#0C5460', label: 'Booked', icon: Calendar },
      active: { bg: '#CCE5FF', text: '#004085', label: 'Active', icon: Navigation },
      maintenance: { bg: '#FFF3CD', text: '#856404', label: 'In Maintenance', icon: Wrench },
      workshop: { bg: '#FFE8CC', text: '#8B5000', label: 'In Workshop', icon: Wrench },
      dormant: { bg: '#E8E8E8', text: '#505050', label: 'Dormant', icon: AlertCircle },
    };
    const config = statusConfig[status] || statusConfig.available;
    const IconComponent = config.icon;

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
        <IconComponent size={12} />
        {config.label}
      </span>
    );
  };

  // FLEET LIST VIEW
  const FleetListView = () => (
    <div style={{ padding: '32px' }}>
      {/* KPI Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(6, 1fr)',
        gap: '16px',
        marginBottom: '28px'
      }}>
        {[
          { label: 'Total Fleet', value: fleetStats.total, icon: Car, color: colors.primary },
          { label: 'Available', value: fleetStats.available, icon: CheckCircle, color: colors.success },
          { label: 'Active', value: fleetStats.active, icon: Navigation, color: colors.info },
          { label: 'Booked', value: fleetStats.booked, icon: Calendar, color: '#6C63FF' },
          { label: 'Maintenance', value: fleetStats.maintenance, icon: Wrench, color: colors.warning },
          { label: 'Expiring Docs', value: fleetStats.expiringDocs, icon: AlertTriangle, color: colors.danger },
        ].map((stat, idx) => (
          <div key={idx} style={{
            backgroundColor: colors.white,
            borderRadius: '12px',
            padding: '20px',
            border: `1px solid ${colors.lightGrey}`,
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
              <div>
                <div style={{ fontSize: '12px', color: colors.mediumGrey, marginBottom: '8px', textTransform: 'uppercase', fontWeight: '600' }}>
                  {stat.label}
                </div>
                <div style={{ fontSize: '28px', fontWeight: '700', color: colors.darkGrey }}>
                  {stat.value}
                </div>
              </div>
              <div style={{
                width: '44px',
                height: '44px',
                backgroundColor: `${stat.color}15`,
                borderRadius: '10px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}>
                <stat.icon size={22} color={stat.color} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Actions Bar - Row 1: Search and Action Buttons */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          backgroundColor: colors.white,
          border: `1px solid ${colors.lightGrey}`,
          borderRadius: '8px',
          padding: '10px 16px',
          gap: '10px',
          width: '350px',
        }}>
          <Search size={18} color={colors.mediumGrey} />
          <input
            type="text"
            placeholder="Search by vehicle ID, name, or registration..."
            style={{ border: 'none', outline: 'none', flex: 1, fontSize: '14px' }}
          />
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={() => {
              // Export fleet data as CSV
              const headers = ['ID', 'Name', 'Type', 'Registration', 'Status', 'Driver', 'Mileage', 'Fuel Level', 'Location'];
              const csvData = fleetVehicles.map(v => [
                v.id,
                v.name,
                v.type,
                v.registrationNo,
                v.status,
                v.assignedDriver || 'Unassigned',
                v.mileage,
                v.fuelLevel + '%',
                v.gps.address
              ]);
              const csvContent = [headers, ...csvData].map(row => row.join(',')).join('\n');
              const blob = new Blob([csvContent], { type: 'text/csv' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `fleet-export-${new Date().toISOString().split('T')[0]}.csv`;
              a.click();
              URL.revokeObjectURL(url);
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 20px',
              backgroundColor: '#E8F5E9',
              color: '#2E7D32',
              border: '2px solid #4CAF50',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '600',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#4CAF50';
              e.currentTarget.style.color = 'white';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = '#E8F5E9';
              e.currentTarget.style.color = '#2E7D32';
            }}
          >
            <Download size={16} />
            Export
          </button>
          <button
            onClick={() => setShowAddVehicleModal(true)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 20px',
              backgroundColor: colors.primary,
              color: 'white',
              border: '2px solid ' + colors.primary,
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '600',
              transition: 'all 0.2s',
              boxShadow: '0 2px 4px rgba(31, 71, 136, 0.3)',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#163560';
              e.currentTarget.style.transform = 'translateY(-1px)';
              e.currentTarget.style.boxShadow = '0 4px 8px rgba(31, 71, 136, 0.4)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = colors.primary;
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 2px 4px rgba(31, 71, 136, 0.3)';
            }}
          >
            <Plus size={16} />
            Add Vehicle
          </button>
        </div>
      </div>

      {/* Actions Bar - Row 2: View Tabs and Status Filters */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        {/* View Mode Tabs */}
        <div style={{
          display: 'flex',
          backgroundColor: colors.white,
          borderRadius: '10px',
          border: `1px solid ${colors.lightGrey}`,
          padding: '4px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
        }}>
          {[
            { id: 'grid', label: 'Grid View', icon: null },
            { id: 'table', label: 'Table View', icon: null },
            { id: 'map', label: 'Live Map', icon: Map },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => tab.id === 'map' ? setFleetSubView('map') : setFleetViewMode(tab.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 20px',
                backgroundColor: (tab.id === 'map' ? false : fleetViewMode === tab.id) ? colors.primary : 'transparent',
                color: (tab.id === 'map' ? false : fleetViewMode === tab.id) ? colors.white : colors.darkGrey,
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '600',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => {
                if ((tab.id === 'map' ? true : fleetViewMode !== tab.id)) {
                  e.currentTarget.style.backgroundColor = '#F0F4F8';
                }
              }}
              onMouseLeave={(e) => {
                if ((tab.id === 'map' ? true : fleetViewMode !== tab.id)) {
                  e.currentTarget.style.backgroundColor = 'transparent';
                }
              }}
            >
              {tab.icon && <tab.icon size={16} />}
              {tab.label}
            </button>
          ))}
        </div>

        {/* Status Filter Tabs */}
        <div style={{ display: 'flex', gap: '6px', backgroundColor: colors.white, padding: '6px', borderRadius: '8px', border: `1px solid ${colors.lightGrey}` }}>
          {['all', 'available', 'active', 'booked', 'maintenance', 'dormant'].map(status => (
            <button
              key={status}
              onClick={() => setFleetStatusFilter(status)}
              style={{
                padding: '6px 14px',
                backgroundColor: fleetStatusFilter === status ? colors.primary : 'transparent',
                color: fleetStatusFilter === status ? colors.white : colors.mediumGrey,
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '13px',
                fontWeight: '600',
                textTransform: 'capitalize',
                transition: 'all 0.2s',
              }}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {/* Grid View */}
      {fleetViewMode === 'grid' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px' }}>
          {filteredFleet.map(vehicle => (
            <div
              key={vehicle.id}
              onClick={() => {
                setSelectedVehicle(vehicle);
                setFleetSubView('details');
              }}
              style={{
                backgroundColor: colors.white,
                borderRadius: '12px',
                overflow: 'hidden',
                border: `1px solid ${colors.lightGrey}`,
                cursor: 'pointer',
                transition: 'all 0.2s',
                boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-4px)';
                e.currentTarget.style.boxShadow = '0 8px 16px rgba(0,0,0,0.1)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.05)';
              }}
            >
              {/* Vehicle Header */}
              <div style={{
                height: '100px',
                backgroundColor: '#F0F4F8',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                position: 'relative',
              }}>
                <Car size={48} color={colors.mediumGrey} />
                <div style={{ position: 'absolute', top: '10px', right: '10px' }}>
                  <VehicleStatusBadge status={vehicle.status} />
                </div>
                {vehicle.gps.ignition && (
                  <div style={{
                    position: 'absolute',
                    top: '10px',
                    left: '10px',
                    backgroundColor: colors.success,
                    borderRadius: '50%',
                    width: '12px',
                    height: '12px',
                    animation: 'pulse 2s infinite',
                  }} title="Ignition On" />
                )}
              </div>

              {/* Vehicle Info */}
              <div style={{ padding: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '8px' }}>
                  <div>
                    <div style={{ fontSize: '11px', color: colors.primary, fontWeight: '700' }}>{vehicle.id}</div>
                    <div style={{ fontSize: '15px', fontWeight: '700', color: colors.darkGrey }}>{vehicle.name}</div>
                  </div>
                </div>

                <div style={{ fontSize: '12px', color: colors.mediumGrey, marginBottom: '12px' }}>
                  {vehicle.registrationNo} • {vehicle.color}
                </div>

                {/* Quick Stats */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(3, 1fr)',
                  gap: '8px',
                  padding: '12px 0',
                  borderTop: `1px solid ${colors.lightGrey}`,
                  borderBottom: `1px solid ${colors.lightGrey}`,
                  marginBottom: '12px',
                }}>
                  <div style={{ textAlign: 'center' }}>
                    <Gauge size={14} color={colors.mediumGrey} />
                    <div style={{ fontSize: '11px', color: colors.mediumGrey, marginTop: '2px' }}>
                      {vehicle.mileage.toLocaleString()} km
                    </div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <Fuel size={14} color={vehicle.fuelLevel < 25 ? colors.danger : colors.mediumGrey} />
                    <div style={{ fontSize: '11px', color: vehicle.fuelLevel < 25 ? colors.danger : colors.mediumGrey, marginTop: '2px' }}>
                      {vehicle.fuelLevel}%
                    </div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <Battery size={14} color={vehicle.batteryVoltage < 12 ? colors.warning : colors.mediumGrey} />
                    <div style={{ fontSize: '11px', color: colors.mediumGrey, marginTop: '2px' }}>
                      {vehicle.batteryVoltage}V
                    </div>
                  </div>
                </div>

                {/* Location or Assignment */}
                <div style={{ fontSize: '12px', color: colors.mediumGrey, display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <MapPin size={12} />
                  {vehicle.gps.address.length > 25 ? vehicle.gps.address.substring(0, 25) + '...' : vehicle.gps.address}
                </div>

                {vehicle.assignedDriver && (
                  <div style={{ fontSize: '12px', color: colors.info, marginTop: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <User size={12} />
                    {vehicle.assignedDriver}
                  </div>
                )}

                {/* Document Alerts */}
                {vehicle.documents.some(d => d.status === 'expiring') && (
                  <div style={{
                    marginTop: '10px',
                    padding: '8px',
                    backgroundColor: '#FFF3CD',
                    borderRadius: '6px',
                    fontSize: '11px',
                    color: '#856404',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                  }}>
                    <AlertTriangle size={12} />
                    {vehicle.documents.filter(d => d.status === 'expiring').length} document(s) expiring soon
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Table View */}
      {fleetViewMode === 'table' && (
        <div style={{ backgroundColor: colors.white, borderRadius: '12px', border: `1px solid ${colors.lightGrey}`, overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: '#F8FAFC', borderBottom: `1px solid ${colors.lightGrey}` }}>
                <th style={{ padding: '14px 16px', textAlign: 'left', fontSize: '12px', fontWeight: '700', color: colors.darkGrey, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Vehicle</th>
                <th style={{ padding: '14px 16px', textAlign: 'left', fontSize: '12px', fontWeight: '700', color: colors.darkGrey, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Registration</th>
                <th style={{ padding: '14px 16px', textAlign: 'left', fontSize: '12px', fontWeight: '700', color: colors.darkGrey, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Status</th>
                <th style={{ padding: '14px 16px', textAlign: 'left', fontSize: '12px', fontWeight: '700', color: colors.darkGrey, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Driver</th>
                <th style={{ padding: '14px 16px', textAlign: 'left', fontSize: '12px', fontWeight: '700', color: colors.darkGrey, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Mileage</th>
                <th style={{ padding: '14px 16px', textAlign: 'left', fontSize: '12px', fontWeight: '700', color: colors.darkGrey, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Fuel</th>
                <th style={{ padding: '14px 16px', textAlign: 'left', fontSize: '12px', fontWeight: '700', color: colors.darkGrey, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Location</th>
                <th style={{ padding: '14px 16px', textAlign: 'center', fontSize: '12px', fontWeight: '700', color: colors.darkGrey, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredFleet.map((vehicle, idx) => (
                <tr
                  key={vehicle.id}
                  style={{
                    borderBottom: idx < filteredFleet.length - 1 ? `1px solid ${colors.lightGrey}` : 'none',
                    cursor: 'pointer',
                    transition: 'background-color 0.2s',
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#F8FAFC'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  onClick={() => { setSelectedVehicle(vehicle); setFleetSubView('details'); }}
                >
                  <td style={{ padding: '14px 16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div style={{ width: '40px', height: '40px', borderRadius: '8px', backgroundColor: '#F0F4F8', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <Car size={18} color={colors.primary} />
                      </div>
                      <div>
                        <div style={{ fontSize: '14px', fontWeight: '600', color: colors.darkGrey }}>{vehicle.name}</div>
                        <div style={{ fontSize: '12px', color: colors.mediumGrey }}>{vehicle.id}</div>
                      </div>
                    </div>
                  </td>
                  <td style={{ padding: '14px 16px', fontSize: '14px', color: colors.darkGrey }}>{vehicle.registrationNo}</td>
                  <td style={{ padding: '14px 16px' }}>
                    <VehicleStatusBadge status={vehicle.status} />
                  </td>
                  <td style={{ padding: '14px 16px', fontSize: '14px', color: vehicle.assignedDriver ? colors.darkGrey : colors.mediumGrey }}>
                    {vehicle.assignedDriver || '—'}
                  </td>
                  <td style={{ padding: '14px 16px', fontSize: '14px', color: colors.darkGrey }}>{vehicle.mileage.toLocaleString()} km</td>
                  <td style={{ padding: '14px 16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <div style={{
                        width: '40px',
                        height: '6px',
                        backgroundColor: '#E5E7EB',
                        borderRadius: '3px',
                        overflow: 'hidden'
                      }}>
                        <div style={{
                          width: `${vehicle.fuelLevel}%`,
                          height: '100%',
                          backgroundColor: vehicle.fuelLevel < 25 ? colors.danger : vehicle.fuelLevel < 50 ? colors.warning : colors.success,
                          borderRadius: '3px',
                        }} />
                      </div>
                      <span style={{ fontSize: '12px', color: vehicle.fuelLevel < 25 ? colors.danger : colors.mediumGrey }}>{vehicle.fuelLevel}%</span>
                    </div>
                  </td>
                  <td style={{ padding: '14px 16px', fontSize: '13px', color: colors.mediumGrey, maxWidth: '150px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <MapPin size={12} />
                      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {vehicle.gps.address.length > 20 ? vehicle.gps.address.substring(0, 20) + '...' : vehicle.gps.address}
                      </span>
                    </div>
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'center' }}>
                    <button
                      onClick={(e) => { e.stopPropagation(); setSelectedVehicle(vehicle); setFleetSubView('details'); }}
                      style={{
                        padding: '6px 12px',
                        backgroundColor: `${colors.primary}15`,
                        color: colors.primary,
                        border: 'none',
                        borderRadius: '6px',
                        fontSize: '12px',
                        fontWeight: '600',
                        cursor: 'pointer',
                      }}
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );

  // ADD VEHICLE MODAL
  const AddVehicleModal = () => {
    if (!showAddVehicleModal) return null;

    const handleSubmit = () => {
      // Generate a new vehicle ID
      const newId = `LA-${String(fleetVehicles.length + 1).padStart(3, '0')}`;
      alert(`✅ Vehicle Added Successfully!\n\nVehicle ID: ${newId}\nName: ${newVehicleForm.make} ${newVehicleForm.model} ${newVehicleForm.year}\nRegistration: ${newVehicleForm.registrationNo}\n\nThe vehicle has been added to your fleet.`);
      setShowAddVehicleModal(false);
      setNewVehicleForm({
        name: '',
        type: 'Sedan',
        make: '',
        model: '',
        year: new Date().getFullYear(),
        registrationNo: '',
        color: '',
        fuelType: 'Petrol',
        transmission: 'Automatic',
        seats: 5,
      });
    };

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
        zIndex: 9999,
      }}>
        <div style={{
          backgroundColor: colors.white,
          borderRadius: '16px',
          width: '600px',
          maxHeight: '90vh',
          overflow: 'auto',
          boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
        }}>
          {/* Header */}
          <div style={{
            padding: '20px 24px',
            borderBottom: `1px solid ${colors.lightGrey}`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <h2 style={{ margin: 0, fontSize: '20px', fontWeight: '700', color: colors.darkGrey, display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Plus size={22} color={colors.primary} />
              Add New Vehicle
            </h2>
            <button
              onClick={() => setShowAddVehicleModal(false)}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                padding: '8px',
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <X size={20} color={colors.mediumGrey} />
            </button>
          </div>

          {/* Form */}
          <div style={{ padding: '24px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              {/* Make */}
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: colors.darkGrey, marginBottom: '6px' }}>Make *</label>
                <input
                  type="text"
                  placeholder="e.g. Toyota"
                  value={newVehicleForm.make}
                  onChange={(e) => setNewVehicleForm({...newVehicleForm, make: e.target.value})}
                  style={{
                    width: '100%',
                    padding: '12px',
                    border: `1px solid ${colors.lightGrey}`,
                    borderRadius: '8px',
                    fontSize: '14px',
                    boxSizing: 'border-box',
                  }}
                />
              </div>
              {/* Model */}
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: colors.darkGrey, marginBottom: '6px' }}>Model *</label>
                <input
                  type="text"
                  placeholder="e.g. Camry"
                  value={newVehicleForm.model}
                  onChange={(e) => setNewVehicleForm({...newVehicleForm, model: e.target.value})}
                  style={{
                    width: '100%',
                    padding: '12px',
                    border: `1px solid ${colors.lightGrey}`,
                    borderRadius: '8px',
                    fontSize: '14px',
                    boxSizing: 'border-box',
                  }}
                />
              </div>
              {/* Year */}
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: colors.darkGrey, marginBottom: '6px' }}>Year *</label>
                <input
                  type="number"
                  min="2000"
                  max="2030"
                  value={newVehicleForm.year}
                  onChange={(e) => setNewVehicleForm({...newVehicleForm, year: parseInt(e.target.value)})}
                  style={{
                    width: '100%',
                    padding: '12px',
                    border: `1px solid ${colors.lightGrey}`,
                    borderRadius: '8px',
                    fontSize: '14px',
                    boxSizing: 'border-box',
                  }}
                />
              </div>
              {/* Registration */}
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: colors.darkGrey, marginBottom: '6px' }}>Registration No *</label>
                <input
                  type="text"
                  placeholder="e.g. LA-009-XYZ"
                  value={newVehicleForm.registrationNo}
                  onChange={(e) => setNewVehicleForm({...newVehicleForm, registrationNo: e.target.value})}
                  style={{
                    width: '100%',
                    padding: '12px',
                    border: `1px solid ${colors.lightGrey}`,
                    borderRadius: '8px',
                    fontSize: '14px',
                    boxSizing: 'border-box',
                  }}
                />
              </div>
              {/* Type */}
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: colors.darkGrey, marginBottom: '6px' }}>Vehicle Type</label>
                <select
                  value={newVehicleForm.type}
                  onChange={(e) => setNewVehicleForm({...newVehicleForm, type: e.target.value})}
                  style={{
                    width: '100%',
                    padding: '12px',
                    border: `1px solid ${colors.lightGrey}`,
                    borderRadius: '8px',
                    fontSize: '14px',
                    boxSizing: 'border-box',
                    backgroundColor: colors.white,
                  }}
                >
                  <option value="Sedan">Sedan</option>
                  <option value="SUV">SUV</option>
                  <option value="Truck">Truck</option>
                  <option value="Bus">Bus</option>
                  <option value="Luxury">Luxury</option>
                </select>
              </div>
              {/* Color */}
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: colors.darkGrey, marginBottom: '6px' }}>Color</label>
                <input
                  type="text"
                  placeholder="e.g. White"
                  value={newVehicleForm.color}
                  onChange={(e) => setNewVehicleForm({...newVehicleForm, color: e.target.value})}
                  style={{
                    width: '100%',
                    padding: '12px',
                    border: `1px solid ${colors.lightGrey}`,
                    borderRadius: '8px',
                    fontSize: '14px',
                    boxSizing: 'border-box',
                  }}
                />
              </div>
              {/* Fuel Type */}
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: colors.darkGrey, marginBottom: '6px' }}>Fuel Type</label>
                <select
                  value={newVehicleForm.fuelType}
                  onChange={(e) => setNewVehicleForm({...newVehicleForm, fuelType: e.target.value})}
                  style={{
                    width: '100%',
                    padding: '12px',
                    border: `1px solid ${colors.lightGrey}`,
                    borderRadius: '8px',
                    fontSize: '14px',
                    boxSizing: 'border-box',
                    backgroundColor: colors.white,
                  }}
                >
                  <option value="Petrol">Petrol</option>
                  <option value="Diesel">Diesel</option>
                  <option value="Electric">Electric</option>
                  <option value="Hybrid">Hybrid</option>
                </select>
              </div>
              {/* Transmission */}
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: colors.darkGrey, marginBottom: '6px' }}>Transmission</label>
                <select
                  value={newVehicleForm.transmission}
                  onChange={(e) => setNewVehicleForm({...newVehicleForm, transmission: e.target.value})}
                  style={{
                    width: '100%',
                    padding: '12px',
                    border: `1px solid ${colors.lightGrey}`,
                    borderRadius: '8px',
                    fontSize: '14px',
                    boxSizing: 'border-box',
                    backgroundColor: colors.white,
                  }}
                >
                  <option value="Automatic">Automatic</option>
                  <option value="Manual">Manual</option>
                </select>
              </div>
              {/* Seats */}
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: colors.darkGrey, marginBottom: '6px' }}>Seats</label>
                <input
                  type="number"
                  min="2"
                  max="50"
                  value={newVehicleForm.seats}
                  onChange={(e) => setNewVehicleForm({...newVehicleForm, seats: parseInt(e.target.value)})}
                  style={{
                    width: '100%',
                    padding: '12px',
                    border: `1px solid ${colors.lightGrey}`,
                    borderRadius: '8px',
                    fontSize: '14px',
                    boxSizing: 'border-box',
                  }}
                />
              </div>
            </div>
          </div>

          {/* Footer */}
          <div style={{
            padding: '16px 24px',
            borderTop: `1px solid ${colors.lightGrey}`,
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '12px',
          }}>
            <button
              onClick={() => setShowAddVehicleModal(false)}
              style={{
                padding: '12px 24px',
                backgroundColor: colors.white,
                color: colors.darkGrey,
                border: `1px solid ${colors.lightGrey}`,
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '600',
              }}
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={!newVehicleForm.make || !newVehicleForm.model || !newVehicleForm.registrationNo}
              style={{
                padding: '12px 24px',
                backgroundColor: (!newVehicleForm.make || !newVehicleForm.model || !newVehicleForm.registrationNo) ? colors.lightGrey : colors.primary,
                color: (!newVehicleForm.make || !newVehicleForm.model || !newVehicleForm.registrationNo) ? colors.mediumGrey : colors.white,
                border: 'none',
                borderRadius: '8px',
                cursor: (!newVehicleForm.make || !newVehicleForm.model || !newVehicleForm.registrationNo) ? 'not-allowed' : 'pointer',
                fontSize: '14px',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <Plus size={16} />
              Add Vehicle
            </button>
          </div>
        </div>
      </div>
    );
  };

  // FLEET VEHICLE DETAILS VIEW
  const FleetVehicleDetailsView = () => {
    if (!selectedVehicle) return null;
    const v = selectedVehicle;

    return (
      <div style={{ padding: '32px' }}>
        {/* Back Button and Actions */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <button
            onClick={() => setFleetSubView('list')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 20px',
              backgroundColor: colors.white,
              border: `1px solid ${colors.lightGrey}`,
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '600',
              color: colors.darkGrey,
            }}
          >
            <ChevronLeft size={18} />
            Back to Fleet
          </button>
          <div style={{ display: 'flex', gap: '12px' }}>
            <Button variant="ghost" icon={Edit}>Edit Vehicle</Button>
            <Button variant="ghost" icon={Wrench}>Schedule Service</Button>
            <Button variant="ghost" icon={FileText}>Documents</Button>
            <Button icon={Navigation}>Track Live</Button>
          </div>
        </div>

        {/* Vehicle Header Card */}
        <div style={{
          backgroundColor: colors.white,
          borderRadius: '16px',
          padding: '28px',
          marginBottom: '24px',
          border: `1px solid ${colors.lightGrey}`,
          boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
        }}>
          <div style={{ display: 'flex', gap: '28px' }}>
            {/* Vehicle Image Placeholder */}
            <div style={{
              width: '220px',
              height: '160px',
              backgroundColor: '#F0F4F8',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}>
              <Car size={72} color={colors.mediumGrey} />
            </div>

            {/* Vehicle Info */}
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '12px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '6px' }}>
                    <span style={{ fontSize: '13px', color: colors.primary, fontWeight: '700', backgroundColor: `${colors.primary}15`, padding: '4px 12px', borderRadius: '6px' }}>
                      {v.id}
                    </span>
                    <VehicleStatusBadge status={v.status} />
                    {v.gps.ignition && (
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', color: colors.success }}>
                        <Circle size={8} fill={colors.success} /> Engine Running
                      </span>
                    )}
                  </div>
                  <h2 style={{ fontSize: '26px', fontWeight: '700', color: colors.darkGrey, margin: '0 0 8px 0' }}>
                    {v.name}
                  </h2>
                  <div style={{ fontSize: '14px', color: colors.mediumGrey }}>
                    {v.make} {v.model} • {v.year} • {v.color} • {v.transmission}
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '32px', marginTop: '20px' }}>
                <div>
                  <div style={{ fontSize: '12px', color: colors.mediumGrey, marginBottom: '4px' }}>Registration</div>
                  <div style={{ fontSize: '15px', fontWeight: '600', color: colors.darkGrey }}>{v.registrationNo}</div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: colors.mediumGrey, marginBottom: '4px' }}>VIN</div>
                  <div style={{ fontSize: '15px', fontWeight: '600', color: colors.darkGrey }}>{v.vin}</div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: colors.mediumGrey, marginBottom: '4px' }}>Fuel Type</div>
                  <div style={{ fontSize: '15px', fontWeight: '600', color: colors.darkGrey }}>{v.fuelType}</div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: colors.mediumGrey, marginBottom: '4px' }}>Seats</div>
                  <div style={{ fontSize: '15px', fontWeight: '600', color: colors.darkGrey }}>{v.seats}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
          {/* Left Column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* Real-time Status */}
            <div style={{
              backgroundColor: colors.white,
              borderRadius: '12px',
              padding: '24px',
              border: `1px solid ${colors.lightGrey}`,
            }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', color: colors.darkGrey, margin: '0 0 20px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Activity size={18} color={colors.primary} /> Real-Time Status
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px' }}>
                <div style={{ textAlign: 'center', padding: '16px', backgroundColor: '#F8F9FA', borderRadius: '10px' }}>
                  <Gauge size={24} color={colors.primary} />
                  <div style={{ fontSize: '22px', fontWeight: '700', color: colors.darkGrey, margin: '8px 0 4px' }}>
                    {v.mileage.toLocaleString()}
                  </div>
                  <div style={{ fontSize: '12px', color: colors.mediumGrey }}>Total KM</div>
                </div>
                <div style={{ textAlign: 'center', padding: '16px', backgroundColor: '#F8F9FA', borderRadius: '10px' }}>
                  <Fuel size={24} color={v.fuelLevel < 25 ? colors.danger : colors.success} />
                  <div style={{ fontSize: '22px', fontWeight: '700', color: v.fuelLevel < 25 ? colors.danger : colors.darkGrey, margin: '8px 0 4px' }}>
                    {v.fuelLevel}%
                  </div>
                  <div style={{ fontSize: '12px', color: colors.mediumGrey }}>Fuel Level</div>
                </div>
                <div style={{ textAlign: 'center', padding: '16px', backgroundColor: '#F8F9FA', borderRadius: '10px' }}>
                  <Battery size={24} color={v.batteryVoltage < 12 ? colors.warning : colors.success} />
                  <div style={{ fontSize: '22px', fontWeight: '700', color: colors.darkGrey, margin: '8px 0 4px' }}>
                    {v.batteryVoltage}V
                  </div>
                  <div style={{ fontSize: '12px', color: colors.mediumGrey }}>Battery</div>
                </div>
                <div style={{ textAlign: 'center', padding: '16px', backgroundColor: '#F8F9FA', borderRadius: '10px' }}>
                  <Navigation size={24} color={colors.info} />
                  <div style={{ fontSize: '22px', fontWeight: '700', color: colors.darkGrey, margin: '8px 0 4px' }}>
                    {v.gps.speed}
                  </div>
                  <div style={{ fontSize: '12px', color: colors.mediumGrey }}>Speed (km/h)</div>
                </div>
              </div>
            </div>

            {/* GPS Location */}
            <div style={{
              backgroundColor: colors.white,
              borderRadius: '12px',
              padding: '24px',
              border: `1px solid ${colors.lightGrey}`,
            }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', color: colors.darkGrey, margin: '0 0 20px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <MapPin size={18} color={colors.primary} /> GPS Location
              </h3>
              <div style={{
                height: '200px',
                backgroundColor: '#E8F4EA',
                borderRadius: '10px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '16px',
                position: 'relative',
              }}>
                <Map size={48} color={colors.success} />
                <div style={{ position: 'absolute', bottom: '12px', left: '12px', backgroundColor: colors.white, padding: '8px 12px', borderRadius: '6px', fontSize: '12px' }}>
                  📍 {v.gps.address}
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
                <div>
                  <div style={{ fontSize: '11px', color: colors.mediumGrey }}>Latitude</div>
                  <div style={{ fontSize: '14px', fontWeight: '600' }}>{v.gps.latitude}</div>
                </div>
                <div>
                  <div style={{ fontSize: '11px', color: colors.mediumGrey }}>Longitude</div>
                  <div style={{ fontSize: '14px', fontWeight: '600' }}>{v.gps.longitude}</div>
                </div>
                <div>
                  <div style={{ fontSize: '11px', color: colors.mediumGrey }}>Heading</div>
                  <div style={{ fontSize: '14px', fontWeight: '600' }}>{v.gps.heading}</div>
                </div>
                <div>
                  <div style={{ fontSize: '11px', color: colors.mediumGrey }}>Signal</div>
                  <div style={{ fontSize: '14px', fontWeight: '600', color: v.gps.signalQuality === 'Good' ? colors.success : colors.warning }}>{v.gps.signalQuality}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* Current Assignment */}
            {v.currentBooking && (
              <div style={{
                backgroundColor: colors.white,
                borderRadius: '12px',
                padding: '24px',
                border: `1px solid ${colors.lightGrey}`,
              }}>
                <h3 style={{ fontSize: '16px', fontWeight: '700', color: colors.darkGrey, margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Calendar size={18} color={colors.primary} /> Current Assignment
                </h3>
                <div style={{ padding: '16px', backgroundColor: '#E8F4FC', borderRadius: '10px' }}>
                  <div style={{ fontSize: '13px', color: colors.info, fontWeight: '600', marginBottom: '8px' }}>{v.currentBooking}</div>
                  <div style={{ fontSize: '15px', fontWeight: '600', color: colors.darkGrey, marginBottom: '8px' }}>{v.currentClient}</div>
                  <div style={{ fontSize: '13px', color: colors.mediumGrey, display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <User size={14} /> {v.assignedDriver}
                  </div>
                </div>
              </div>
            )}

            {/* Documents Status */}
            <div style={{
              backgroundColor: colors.white,
              borderRadius: '12px',
              padding: '24px',
              border: `1px solid ${colors.lightGrey}`,
            }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', color: colors.darkGrey, margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FileCheck size={18} color={colors.primary} /> Documents
              </h3>
              {v.documents.map((doc, idx) => (
                <div key={idx} style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '12px 0',
                  borderBottom: idx < v.documents.length - 1 ? `1px solid ${colors.lightGrey}` : 'none',
                }}>
                  <div>
                    <div style={{ fontSize: '14px', fontWeight: '500', color: colors.darkGrey }}>{doc.type}</div>
                    <div style={{ fontSize: '12px', color: colors.mediumGrey }}>Expires: {doc.expiry}</div>
                  </div>
                  <span style={{
                    padding: '4px 10px',
                    borderRadius: '12px',
                    fontSize: '11px',
                    fontWeight: '600',
                    backgroundColor: doc.status === 'valid' ? '#D4EDDA' : '#FFF3CD',
                    color: doc.status === 'valid' ? '#155724' : '#856404',
                  }}>
                    {doc.status === 'valid' ? 'Valid' : 'Expiring Soon'}
                  </span>
                </div>
              ))}
            </div>

            {/* Maintenance History */}
            <div style={{
              backgroundColor: colors.white,
              borderRadius: '12px',
              padding: '24px',
              border: `1px solid ${colors.lightGrey}`,
            }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', color: colors.darkGrey, margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Wrench size={18} color={colors.primary} /> Maintenance History
              </h3>
              {v.maintenanceHistory.length > 0 ? v.maintenanceHistory.map((m, idx) => (
                <div key={idx} style={{
                  padding: '12px 0',
                  borderBottom: idx < v.maintenanceHistory.length - 1 ? `1px solid ${colors.lightGrey}` : 'none',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <div style={{ fontSize: '14px', fontWeight: '500', color: colors.darkGrey }}>{m.type}</div>
                    <div style={{ fontSize: '13px', fontWeight: '600', color: colors.primary }}>₦{m.cost.toLocaleString()}</div>
                  </div>
                  <div style={{ fontSize: '12px', color: colors.mediumGrey, marginTop: '4px' }}>
                    {m.date} • {m.vendor} • {m.mileage.toLocaleString()} km
                  </div>
                </div>
              )) : (
                <div style={{ fontSize: '13px', color: colors.mediumGrey, textAlign: 'center', padding: '20px' }}>
                  No maintenance records yet
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  // SHOWCASE/CLIENT BOOKING VIEW
  const ShowcaseView = () => {
    const bookingTotals = calculateBookingTotal();

    // Browse View - Vehicle Grid
    if (showcaseView === 'browse') {
      return (
        <div style={{ padding: '0' }}>
          {/* Hero Section */}
          <div style={{
            background: `linear-gradient(135deg, ${colors.primary} 0%, ${colors.secondary} 100%)`,
            padding: '60px 40px',
            color: colors.white,
            textAlign: 'center',
          }}>
            <h1 style={{ fontSize: '36px', fontWeight: '700', margin: '0 0 12px 0' }}>
              Premium Vehicle Rental
            </h1>
            <p style={{ fontSize: '18px', opacity: 0.9, margin: 0 }}>
              Choose from our fleet of well-maintained vehicles for your business or personal needs
            </p>
          </div>

          {/* Filters */}
          <div style={{ padding: '24px 40px', backgroundColor: colors.white, borderBottom: `1px solid ${colors.lightGrey}` }}>
            {/* Vehicle Type Filters */}
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '16px' }}>
              <span style={{ fontSize: '13px', fontWeight: '600', color: colors.mediumGrey, minWidth: '80px' }}>Vehicle Type:</span>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {['all', 'Sedan', 'SUV', 'Luxury', 'Bus', 'Truck'].map(type => (
                  <button
                    key={type}
                    onClick={() => setShowcaseFilter({ ...showcaseFilter, type })}
                    style={{
                      padding: '8px 18px',
                      backgroundColor: showcaseFilter.type === type ? colors.primary : colors.white,
                      color: showcaseFilter.type === type ? colors.white : colors.darkGrey,
                      border: `1px solid ${showcaseFilter.type === type ? colors.primary : colors.lightGrey}`,
                      borderRadius: '20px',
                      cursor: 'pointer',
                      fontSize: '13px',
                      fontWeight: '600',
                      transition: 'all 0.2s',
                    }}
                  >
                    {type === 'all' ? 'All Types' : type}
                  </button>
                ))}
              </div>
            </div>
            {/* Price Range Filters */}
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
              <span style={{ fontSize: '13px', fontWeight: '600', color: colors.mediumGrey, minWidth: '80px' }}>Price Range:</span>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {[
                  { value: 'all', label: 'All Prices' },
                  { value: 'budget', label: 'Budget (Under ₦40k)' },
                  { value: 'mid', label: 'Mid-Range (₦40k - ₦70k)' },
                  { value: 'premium', label: 'Premium (Above ₦70k)' },
                ].map(range => (
                  <button
                    key={range.value}
                    onClick={() => setShowcaseFilter({ ...showcaseFilter, priceRange: range.value })}
                    style={{
                      padding: '8px 18px',
                      backgroundColor: showcaseFilter.priceRange === range.value ? colors.accent : colors.white,
                      color: showcaseFilter.priceRange === range.value ? colors.white : colors.darkGrey,
                      border: `1px solid ${showcaseFilter.priceRange === range.value ? colors.accent : colors.lightGrey}`,
                      borderRadius: '20px',
                      cursor: 'pointer',
                      fontSize: '13px',
                      fontWeight: '600',
                      transition: 'all 0.2s',
                    }}
                  >
                    {range.label}
                  </button>
                ))}
              </div>
              <span style={{ marginLeft: 'auto', fontSize: '14px', color: colors.mediumGrey, fontWeight: '500' }}>
                {filteredShowcaseVehicles.length} vehicles available
              </span>
            </div>
          </div>

          {/* Vehicle Grid */}
          <div style={{ padding: '32px 40px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '24px' }}>
              {filteredShowcaseVehicles.map(vehicle => (
                <div
                  key={vehicle.id}
                  onClick={() => {
                    setSelectedShowcaseVehicle(vehicle);
                    setShowcaseView('vehicle');
                  }}
                  style={{
                    backgroundColor: colors.white,
                    borderRadius: '16px',
                    overflow: 'hidden',
                    border: `1px solid ${colors.lightGrey}`,
                    cursor: 'pointer',
                    transition: 'all 0.3s',
                    opacity: vehicle.available ? 1 : 0.6,
                  }}
                  onMouseEnter={(e) => {
                    if (vehicle.available) {
                      e.currentTarget.style.transform = 'translateY(-8px)';
                      e.currentTarget.style.boxShadow = '0 12px 24px rgba(0,0,0,0.15)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = 'none';
                  }}
                >
                  <div style={{ height: '160px', backgroundColor: '#F0F4F8', overflow: 'hidden' }}>
                    <img
                      src={vehicle.image}
                      alt={vehicle.name}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      onError={(e) => { e.target.style.display = 'none'; }}
                    />
                  </div>
                  <div style={{ padding: '20px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '10px' }}>
                      <span style={{ fontSize: '11px', color: colors.primary, fontWeight: '700', backgroundColor: `${colors.primary}15`, padding: '5px 12px', borderRadius: '12px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                        {vehicle.type}
                      </span>
                      <span style={{ fontSize: '13px', color: '#FFB800', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: '600' }}>
                        ★ {vehicle.rating}
                      </span>
                    </div>
                    <h3 style={{ fontSize: '17px', fontWeight: '700', color: colors.darkGrey, margin: '0 0 12px 0' }}>
                      {vehicle.name}
                    </h3>
                    {/* Feature Badges */}
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '14px' }}>
                      <span style={{ fontSize: '11px', color: colors.darkGrey, backgroundColor: '#F0F4F8', padding: '5px 10px', borderRadius: '12px', fontWeight: '500' }}>
                        {vehicle.seats} seats
                      </span>
                      {vehicle.features.slice(0, 2).map((feature, idx) => (
                        <span key={idx} style={{ fontSize: '11px', color: colors.darkGrey, backgroundColor: '#F0F4F8', padding: '5px 10px', borderRadius: '12px', fontWeight: '500' }}>
                          {feature}
                        </span>
                      ))}
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <span style={{ fontSize: '20px', fontWeight: '700', color: colors.primary }}>
                          ₦{vehicle.dailyRate.toLocaleString()}
                        </span>
                        <span style={{ fontSize: '13px', color: colors.mediumGrey }}>/day</span>
                      </div>
                      {!vehicle.available && (
                        <span style={{ fontSize: '11px', color: colors.white, backgroundColor: colors.danger, padding: '4px 10px', borderRadius: '10px', fontWeight: '600' }}>Unavailable</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      );
    }

    // Vehicle Detail View
    if (showcaseView === 'vehicle' && selectedShowcaseVehicle) {
      const v = selectedShowcaseVehicle;
      const recommendations = showcaseVehicles.filter(sv => sv.type === v.type && sv.id !== v.id && sv.available).slice(0, 3);

      return (
        <div style={{ padding: '32px 40px' }}>
          <button
            onClick={() => setShowcaseView('browse')}
            style={{
              display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 20px',
              backgroundColor: colors.white, border: `1px solid ${colors.lightGrey}`,
              borderRadius: '8px', cursor: 'pointer', fontSize: '14px', fontWeight: '600',
              color: colors.darkGrey, marginBottom: '24px',
            }}
          >
            <ChevronLeft size={18} /> Back to Vehicles
          </button>

          <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '32px' }}>
            {/* Left - Vehicle Details */}
            <div>
              <div style={{ borderRadius: '16px', overflow: 'hidden', marginBottom: '24px', height: '350px', backgroundColor: '#F0F4F8' }}>
                <img src={v.image} alt={v.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} onError={(e) => { e.target.style.display = 'none'; }} />
              </div>
              <h1 style={{ fontSize: '28px', fontWeight: '700', color: colors.darkGrey, margin: '0 0 16px 0' }}>{v.name}</h1>

              {/* Vehicle Info Badges */}
              <div style={{ display: 'flex', gap: '10px', marginBottom: '24px', flexWrap: 'wrap' }}>
                <span style={{ fontSize: '12px', color: colors.primary, fontWeight: '700', backgroundColor: `${colors.primary}15`, padding: '8px 16px', borderRadius: '20px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  {v.type}
                </span>
                <span style={{ fontSize: '13px', color: '#856404', backgroundColor: '#FFF3CD', padding: '8px 16px', borderRadius: '20px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  ★ {v.rating} Rating
                </span>
                <span style={{ fontSize: '13px', color: colors.darkGrey, backgroundColor: '#F0F4F8', padding: '8px 16px', borderRadius: '20px', fontWeight: '600' }}>
                  {v.seats} Seats
                </span>
              </div>

              <h3 style={{ fontSize: '16px', fontWeight: '600', color: colors.darkGrey, marginBottom: '12px' }}>Features</h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginBottom: '24px' }}>
                {v.features.map((f, i) => (
                  <span key={i} style={{ padding: '10px 18px', backgroundColor: '#F0F4F8', borderRadius: '20px', fontSize: '13px', fontWeight: '500', color: colors.darkGrey, border: `1px solid ${colors.lightGrey}` }}>{f}</span>
                ))}
              </div>
            </div>

            {/* Right - Booking Form */}
            <div style={{ backgroundColor: colors.white, borderRadius: '16px', padding: '28px', border: `1px solid ${colors.lightGrey}`, height: 'fit-content' }}>
              <div style={{ fontSize: '28px', fontWeight: '700', color: colors.primary, marginBottom: '4px' }}>
                ₦{v.dailyRate.toLocaleString()}<span style={{ fontSize: '16px', color: colors.mediumGrey, fontWeight: '400' }}>/day</span>
              </div>
              <div style={{ fontSize: '13px', color: colors.mediumGrey, marginBottom: '24px' }}>Inclusive of basic insurance</div>

              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontSize: '13px', fontWeight: '600', color: colors.darkGrey, display: 'block', marginBottom: '6px' }}>Pickup Date</label>
                <input type="date" value={clientBooking.pickupDate} onChange={(e) => setClientBooking({ ...clientBooking, pickupDate: e.target.value })}
                  style={{ width: '100%', padding: '12px', borderRadius: '8px', border: `1px solid ${colors.lightGrey}`, fontSize: '14px' }} />
              </div>
              <div style={{ marginBottom: '20px' }}>
                <label style={{ fontSize: '13px', fontWeight: '600', color: colors.darkGrey, display: 'block', marginBottom: '6px' }}>Return Date</label>
                <input type="date" value={clientBooking.returnDate} onChange={(e) => setClientBooking({ ...clientBooking, returnDate: e.target.value })}
                  style={{ width: '100%', padding: '12px', borderRadius: '8px', border: `1px solid ${colors.lightGrey}`, fontSize: '14px' }} />
              </div>

              <div style={{ marginBottom: '20px' }}>
                <label style={{ fontSize: '13px', fontWeight: '600', color: colors.darkGrey, display: 'block', marginBottom: '10px' }}>Add-ons</label>
                {[
                  { key: 'withDriver', label: 'Professional Driver', price: '₦5,000/day', icon: User },
                  { key: 'withInsurance', label: 'Full Insurance', price: '₦2,500/day', icon: Shield },
                  { key: 'withFuel', label: 'Full Fuel Tank', price: '₦15,000', icon: Fuel },
                  { key: 'withGPS', label: 'GPS Navigation', price: '₦1,000/day', icon: Navigation },
                ].map(addon => (
                  <label key={addon.key} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '12px', backgroundColor: clientBooking[addon.key] ? `${colors.primary}10` : '#F8F9FA', borderRadius: '8px', marginBottom: '8px', cursor: 'pointer' }}>
                    <input type="checkbox" checked={clientBooking[addon.key]} onChange={(e) => setClientBooking({ ...clientBooking, [addon.key]: e.target.checked })} />
                    <addon.icon size={16} color={colors.primary} />
                    <span style={{ flex: 1, fontSize: '14px' }}>{addon.label}</span>
                    <span style={{ fontSize: '13px', color: colors.mediumGrey }}>{addon.price}</span>
                  </label>
                ))}
              </div>

              {bookingTotals.days > 0 && (
                <div style={{ padding: '16px', backgroundColor: '#F8F9FA', borderRadius: '10px', marginBottom: '20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '14px' }}>
                    <span>Base ({bookingTotals.days} days)</span><span>₦{bookingTotals.baseAmount?.toLocaleString()}</span>
                  </div>
                  {bookingTotals.driverFee > 0 && <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '14px' }}><span>Driver</span><span>₦{bookingTotals.driverFee.toLocaleString()}</span></div>}
                  {bookingTotals.insuranceFee > 0 && <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '14px' }}><span>Insurance</span><span>₦{bookingTotals.insuranceFee.toLocaleString()}</span></div>}
                  {bookingTotals.fuelFee > 0 && <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '14px' }}><span>Fuel</span><span>₦{bookingTotals.fuelFee.toLocaleString()}</span></div>}
                  {bookingTotals.gpsFee > 0 && <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '14px' }}><span>GPS</span><span>₦{bookingTotals.gpsFee.toLocaleString()}</span></div>}
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '14px', color: colors.mediumGrey }}><span>VAT (7.5%)</span><span>₦{bookingTotals.vat?.toLocaleString()}</span></div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: '700', fontSize: '16px', paddingTop: '8px', borderTop: `1px solid ${colors.lightGrey}` }}>
                    <span>Total</span><span style={{ color: colors.primary }}>₦{bookingTotals.total?.toLocaleString()}</span>
                  </div>
                </div>
              )}

              <button
                onClick={() => setShowcaseView('form')}
                disabled={!clientBooking.pickupDate || !clientBooking.returnDate}
                style={{
                  width: '100%', padding: '16px', backgroundColor: colors.primary, color: colors.white,
                  border: 'none', borderRadius: '10px', fontSize: '16px', fontWeight: '700', cursor: 'pointer',
                  opacity: (!clientBooking.pickupDate || !clientBooking.returnDate) ? 0.7 : 1,
                }}
              >
                Continue to Book
              </button>
            </div>
          </div>

          {/* Recommendations */}
          {recommendations.length > 0 && (
            <div style={{ marginTop: '48px' }}>
              <h3 style={{ fontSize: '20px', fontWeight: '700', color: colors.darkGrey, marginBottom: '20px' }}>You might also be interested in</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px' }}>
                {recommendations.map(rv => (
                  <div key={rv.id} onClick={() => { setSelectedShowcaseVehicle(rv); window.scrollTo(0, 0); }}
                    style={{ backgroundColor: colors.white, borderRadius: '12px', overflow: 'hidden', border: `1px solid ${colors.lightGrey}`, cursor: 'pointer', transition: 'all 0.2s' }}
                    onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-4px)'}
                    onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}>
                    <div style={{ height: '120px', backgroundColor: '#F0F4F8' }}>
                      <img src={rv.image} alt={rv.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} onError={(e) => { e.target.style.display = 'none'; }} />
                    </div>
                    <div style={{ padding: '16px' }}>
                      <div style={{ fontSize: '15px', fontWeight: '600', color: colors.darkGrey }}>{rv.name}</div>
                      <div style={{ fontSize: '14px', color: colors.primary, fontWeight: '700', marginTop: '4px' }}>₦{rv.dailyRate.toLocaleString()}/day</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      );
    }

    // Customer Details Form
    if (showcaseView === 'form' && selectedShowcaseVehicle) {
      return (
        <div style={{ padding: '32px 40px', maxWidth: '900px', margin: '0 auto' }}>
          <button onClick={() => setShowcaseView('vehicle')} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 20px', backgroundColor: colors.white, border: `1px solid ${colors.lightGrey}`, borderRadius: '8px', cursor: 'pointer', fontSize: '14px', fontWeight: '600', color: colors.darkGrey, marginBottom: '24px' }}>
            <ChevronLeft size={18} /> Back
          </button>

          <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '32px' }}>
            <div style={{ backgroundColor: colors.white, borderRadius: '16px', padding: '32px', border: `1px solid ${colors.lightGrey}` }}>
              <h2 style={{ fontSize: '22px', fontWeight: '700', color: colors.darkGrey, margin: '0 0 24px 0' }}>Customer Details</h2>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                <div>
                  <label style={{ fontSize: '13px', fontWeight: '600', color: colors.darkGrey, display: 'block', marginBottom: '6px' }}>Full Name *</label>
                  <input type="text" value={clientBooking.customerName} onChange={(e) => setClientBooking({ ...clientBooking, customerName: e.target.value })}
                    placeholder="John Doe" style={{ width: '100%', padding: '12px', borderRadius: '8px', border: `1px solid ${colors.lightGrey}`, fontSize: '14px' }} />
                </div>
                <div>
                  <label style={{ fontSize: '13px', fontWeight: '600', color: colors.darkGrey, display: 'block', marginBottom: '6px' }}>Company</label>
                  <input type="text" value={clientBooking.customerCompany} onChange={(e) => setClientBooking({ ...clientBooking, customerCompany: e.target.value })}
                    placeholder="Acme Corporation" style={{ width: '100%', padding: '12px', borderRadius: '8px', border: `1px solid ${colors.lightGrey}`, fontSize: '14px' }} />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                <div>
                  <label style={{ fontSize: '13px', fontWeight: '600', color: colors.darkGrey, display: 'block', marginBottom: '6px' }}>Email *</label>
                  <input type="email" value={clientBooking.customerEmail} onChange={(e) => setClientBooking({ ...clientBooking, customerEmail: e.target.value })}
                    placeholder="john@email.com" style={{ width: '100%', padding: '12px', borderRadius: '8px', border: `1px solid ${colors.lightGrey}`, fontSize: '14px' }} />
                </div>
                <div>
                  <label style={{ fontSize: '13px', fontWeight: '600', color: colors.darkGrey, display: 'block', marginBottom: '6px' }}>Phone *</label>
                  <input type="tel" value={clientBooking.customerPhone} onChange={(e) => setClientBooking({ ...clientBooking, customerPhone: e.target.value })}
                    placeholder="0801-234-5678" style={{ width: '100%', padding: '12px', borderRadius: '8px', border: `1px solid ${colors.lightGrey}`, fontSize: '14px' }} />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                <div>
                  <label style={{ fontSize: '13px', fontWeight: '600', color: colors.darkGrey, display: 'block', marginBottom: '6px' }}>Pickup Location *</label>
                  <input type="text" value={clientBooking.pickupLocation} onChange={(e) => setClientBooking({ ...clientBooking, pickupLocation: e.target.value })}
                    placeholder="Victoria Island, Lagos" style={{ width: '100%', padding: '12px', borderRadius: '8px', border: `1px solid ${colors.lightGrey}`, fontSize: '14px' }} />
                </div>
                <div>
                  <label style={{ fontSize: '13px', fontWeight: '600', color: colors.darkGrey, display: 'block', marginBottom: '6px' }}>Return Location</label>
                  <input type="text" value={clientBooking.returnLocation} onChange={(e) => setClientBooking({ ...clientBooking, returnLocation: e.target.value })}
                    placeholder="Same as pickup" style={{ width: '100%', padding: '12px', borderRadius: '8px', border: `1px solid ${colors.lightGrey}`, fontSize: '14px' }} />
                </div>
              </div>

              <div>
                <label style={{ fontSize: '13px', fontWeight: '600', color: colors.darkGrey, display: 'block', marginBottom: '6px' }}>Special Requests</label>
                <textarea value={clientBooking.notes} onChange={(e) => setClientBooking({ ...clientBooking, notes: e.target.value })}
                  placeholder="Any special requirements..." rows={3} style={{ width: '100%', padding: '12px', borderRadius: '8px', border: `1px solid ${colors.lightGrey}`, fontSize: '14px', resize: 'vertical' }} />
              </div>
            </div>

            {/* Booking Summary */}
            <div style={{ backgroundColor: colors.white, borderRadius: '16px', padding: '28px', border: `1px solid ${colors.lightGrey}`, height: 'fit-content' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '700', color: colors.darkGrey, margin: '0 0 20px 0' }}>Booking Summary</h3>

              {/* Vehicle Info */}
              <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', paddingBottom: '16px', borderBottom: `1px solid ${colors.lightGrey}` }}>
                <div style={{ width: '80px', height: '60px', borderRadius: '8px', overflow: 'hidden', backgroundColor: '#F0F4F8' }}>
                  <img src={selectedShowcaseVehicle.image} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                </div>
                <div>
                  <div style={{ fontSize: '15px', fontWeight: '600', color: colors.darkGrey }}>{selectedShowcaseVehicle.name}</div>
                  <div style={{ fontSize: '13px', color: colors.mediumGrey }}>{bookingTotals.days} day{bookingTotals.days > 1 ? 's' : ''}</div>
                  <div style={{ fontSize: '12px', color: colors.mediumGrey }}>{clientBooking.pickupDate} → {clientBooking.returnDate}</div>
                </div>
              </div>

              {/* Price Breakdown */}
              <div style={{ marginBottom: '20px' }}>
                <h4 style={{ fontSize: '13px', fontWeight: '700', color: colors.darkGrey, marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Price Breakdown</h4>

                {/* Line Items */}
                <div style={{ backgroundColor: '#F8FAFC', borderRadius: '12px', overflow: 'hidden', border: `1px solid ${colors.lightGrey}` }}>
                  {/* Base */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 16px', borderBottom: `1px solid ${colors.lightGrey}` }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: `${colors.primary}15`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <Car size={16} color={colors.primary} />
                      </div>
                      <div>
                        <div style={{ fontSize: '14px', fontWeight: '600', color: colors.darkGrey }}>Base Rental</div>
                        <div style={{ fontSize: '12px', color: colors.mediumGrey }}>{bookingTotals.days} day{bookingTotals.days > 1 ? 's' : ''} × ₦{selectedShowcaseVehicle?.dailyRate?.toLocaleString()}</div>
                      </div>
                    </div>
                    <span style={{ fontSize: '14px', fontWeight: '700', color: colors.darkGrey }}>₦{bookingTotals.baseAmount?.toLocaleString()}</span>
                  </div>

                  {/* Driver */}
                  {bookingTotals.driverFee > 0 && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 16px', borderBottom: `1px solid ${colors.lightGrey}` }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: '#E8F5E9', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <User size={16} color="#2E7D32" />
                        </div>
                        <div>
                          <div style={{ fontSize: '14px', fontWeight: '600', color: colors.darkGrey }}>Professional Driver</div>
                          <div style={{ fontSize: '12px', color: colors.mediumGrey }}>{bookingTotals.days} day{bookingTotals.days > 1 ? 's' : ''} × ₦5,000</div>
                        </div>
                      </div>
                      <span style={{ fontSize: '14px', fontWeight: '700', color: colors.darkGrey }}>₦{bookingTotals.driverFee.toLocaleString()}</span>
                    </div>
                  )}

                  {/* Insurance */}
                  {bookingTotals.insuranceFee > 0 && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 16px', borderBottom: `1px solid ${colors.lightGrey}` }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: '#E3F2FD', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <Shield size={16} color="#1565C0" />
                        </div>
                        <div>
                          <div style={{ fontSize: '14px', fontWeight: '600', color: colors.darkGrey }}>Full Insurance</div>
                          <div style={{ fontSize: '12px', color: colors.mediumGrey }}>{bookingTotals.days} day{bookingTotals.days > 1 ? 's' : ''} × ₦2,500</div>
                        </div>
                      </div>
                      <span style={{ fontSize: '14px', fontWeight: '700', color: colors.darkGrey }}>₦{bookingTotals.insuranceFee.toLocaleString()}</span>
                    </div>
                  )}

                  {/* Fuel */}
                  {bookingTotals.fuelFee > 0 && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 16px', borderBottom: `1px solid ${colors.lightGrey}` }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: '#FFF3E0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <Fuel size={16} color="#E65100" />
                        </div>
                        <div>
                          <div style={{ fontSize: '14px', fontWeight: '600', color: colors.darkGrey }}>Full Fuel Tank</div>
                          <div style={{ fontSize: '12px', color: colors.mediumGrey }}>One-time charge</div>
                        </div>
                      </div>
                      <span style={{ fontSize: '14px', fontWeight: '700', color: colors.darkGrey }}>₦{bookingTotals.fuelFee.toLocaleString()}</span>
                    </div>
                  )}

                  {/* GPS */}
                  {bookingTotals.gpsFee > 0 && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 16px', borderBottom: `1px solid ${colors.lightGrey}` }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: '#F3E5F5', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <Navigation size={16} color="#7B1FA2" />
                        </div>
                        <div>
                          <div style={{ fontSize: '14px', fontWeight: '600', color: colors.darkGrey }}>GPS Navigation</div>
                          <div style={{ fontSize: '12px', color: colors.mediumGrey }}>{bookingTotals.days} day{bookingTotals.days > 1 ? 's' : ''} × ₦1,000</div>
                        </div>
                      </div>
                      <span style={{ fontSize: '14px', fontWeight: '700', color: colors.darkGrey }}>₦{bookingTotals.gpsFee.toLocaleString()}</span>
                    </div>
                  )}

                  {/* VAT */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', backgroundColor: '#FAFAFA' }}>
                    <span style={{ fontSize: '13px', color: colors.mediumGrey }}>VAT (7.5%)</span>
                    <span style={{ fontSize: '13px', color: colors.mediumGrey }}>₦{bookingTotals.vat?.toLocaleString()}</span>
                  </div>
                </div>

                {/* Total */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px', marginTop: '12px', backgroundColor: `${colors.primary}10`, borderRadius: '12px', border: `2px solid ${colors.primary}` }}>
                  <span style={{ fontSize: '16px', fontWeight: '700', color: colors.darkGrey }}>Total Amount</span>
                  <span style={{ fontSize: '22px', fontWeight: '800', color: colors.primary }}>₦{bookingTotals.total?.toLocaleString()}</span>
                </div>
              </div>

              <button
                onClick={() => { setBookingReference(`CNI-${Date.now().toString().slice(-8)}`); setShowcaseView('confirmation'); }}
                disabled={!clientBooking.customerName || !clientBooking.customerEmail || !clientBooking.customerPhone || !clientBooking.pickupLocation}
                style={{ width: '100%', padding: '16px', backgroundColor: colors.primary, color: colors.white, border: 'none', borderRadius: '10px', fontSize: '16px', fontWeight: '700', cursor: 'pointer', opacity: (!clientBooking.customerName || !clientBooking.customerEmail || !clientBooking.customerPhone || !clientBooking.pickupLocation) ? 0.7 : 1 }}>
                Confirm Booking
              </button>
            </div>
          </div>
        </div>
      );
    }

    // Confirmation View
    if (showcaseView === 'confirmation' && selectedShowcaseVehicle) {
      return (
        <div style={{ padding: '60px 40px', textAlign: 'center' }}>
          <div style={{ backgroundColor: colors.white, borderRadius: '20px', padding: '48px', maxWidth: '700px', margin: '0 auto', border: `1px solid ${colors.lightGrey}` }}>
            <div style={{ width: '80px', height: '80px', backgroundColor: '#D4EDDA', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 24px' }}>
              <CheckCircle size={40} color="#155724" />
            </div>
            <h1 style={{ fontSize: '28px', fontWeight: '700', color: colors.darkGrey, margin: '0 0 12px 0' }}>Booking Confirmed!</h1>
            <p style={{ fontSize: '16px', color: colors.mediumGrey, marginBottom: '24px' }}>Your booking reference is</p>
            <div style={{ fontSize: '32px', fontWeight: '700', color: colors.primary, backgroundColor: `${colors.primary}15`, padding: '16px 32px', borderRadius: '12px', display: 'inline-block', marginBottom: '32px' }}>
              {bookingReference}
            </div>

            {/* Booking Details */}
            <div style={{ textAlign: 'left', padding: '24px', backgroundColor: '#F8F9FA', borderRadius: '12px', marginBottom: '24px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', color: colors.darkGrey }}>Booking Details</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', fontSize: '14px', marginBottom: '20px' }}>
                <div><span style={{ color: colors.mediumGrey }}>Vehicle:</span> <strong>{selectedShowcaseVehicle.name}</strong></div>
                <div><span style={{ color: colors.mediumGrey }}>Duration:</span> <strong>{bookingTotals.days} day{bookingTotals.days > 1 ? 's' : ''}</strong></div>
                <div><span style={{ color: colors.mediumGrey }}>Pickup:</span> <strong>{clientBooking.pickupDate}</strong></div>
                <div><span style={{ color: colors.mediumGrey }}>Return:</span> <strong>{clientBooking.returnDate}</strong></div>
                <div><span style={{ color: colors.mediumGrey }}>Customer:</span> <strong>{clientBooking.customerName}</strong></div>
                <div><span style={{ color: colors.mediumGrey }}>Location:</span> <strong>{clientBooking.pickupLocation}</strong></div>
              </div>

              {/* Price Breakdown */}
              <div style={{ borderTop: `1px solid ${colors.lightGrey}`, paddingTop: '16px' }}>
                <h4 style={{ fontSize: '13px', fontWeight: '700', color: colors.darkGrey, marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Price Breakdown</h4>

                {/* Line Items */}
                <div style={{ backgroundColor: colors.white, borderRadius: '12px', overflow: 'hidden', border: `1px solid ${colors.lightGrey}` }}>
                  {/* Base */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 14px', borderBottom: `1px solid ${colors.lightGrey}` }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{ width: '28px', height: '28px', borderRadius: '6px', backgroundColor: `${colors.primary}15`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <Car size={14} color={colors.primary} />
                      </div>
                      <div>
                        <div style={{ fontSize: '13px', fontWeight: '600', color: colors.darkGrey }}>Base Rental</div>
                        <div style={{ fontSize: '11px', color: colors.mediumGrey }}>{bookingTotals.days} day{bookingTotals.days > 1 ? 's' : ''} × ₦{selectedShowcaseVehicle?.dailyRate?.toLocaleString()}</div>
                      </div>
                    </div>
                    <span style={{ fontSize: '13px', fontWeight: '700', color: colors.darkGrey }}>₦{bookingTotals.baseAmount?.toLocaleString()}</span>
                  </div>

                  {/* Driver */}
                  {bookingTotals.driverFee > 0 && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 14px', borderBottom: `1px solid ${colors.lightGrey}` }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div style={{ width: '28px', height: '28px', borderRadius: '6px', backgroundColor: '#E8F5E9', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <User size={14} color="#2E7D32" />
                        </div>
                        <div>
                          <div style={{ fontSize: '13px', fontWeight: '600', color: colors.darkGrey }}>Professional Driver</div>
                          <div style={{ fontSize: '11px', color: colors.mediumGrey }}>{bookingTotals.days} day{bookingTotals.days > 1 ? 's' : ''} × ₦5,000</div>
                        </div>
                      </div>
                      <span style={{ fontSize: '13px', fontWeight: '700', color: colors.darkGrey }}>₦{bookingTotals.driverFee.toLocaleString()}</span>
                    </div>
                  )}

                  {/* Insurance */}
                  {bookingTotals.insuranceFee > 0 && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 14px', borderBottom: `1px solid ${colors.lightGrey}` }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div style={{ width: '28px', height: '28px', borderRadius: '6px', backgroundColor: '#E3F2FD', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <Shield size={14} color="#1565C0" />
                        </div>
                        <div>
                          <div style={{ fontSize: '13px', fontWeight: '600', color: colors.darkGrey }}>Full Insurance</div>
                          <div style={{ fontSize: '11px', color: colors.mediumGrey }}>{bookingTotals.days} day{bookingTotals.days > 1 ? 's' : ''} × ₦2,500</div>
                        </div>
                      </div>
                      <span style={{ fontSize: '13px', fontWeight: '700', color: colors.darkGrey }}>₦{bookingTotals.insuranceFee.toLocaleString()}</span>
                    </div>
                  )}

                  {/* Fuel */}
                  {bookingTotals.fuelFee > 0 && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 14px', borderBottom: `1px solid ${colors.lightGrey}` }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div style={{ width: '28px', height: '28px', borderRadius: '6px', backgroundColor: '#FFF3E0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <Fuel size={14} color="#E65100" />
                        </div>
                        <div>
                          <div style={{ fontSize: '13px', fontWeight: '600', color: colors.darkGrey }}>Full Fuel Tank</div>
                          <div style={{ fontSize: '11px', color: colors.mediumGrey }}>One-time charge</div>
                        </div>
                      </div>
                      <span style={{ fontSize: '13px', fontWeight: '700', color: colors.darkGrey }}>₦{bookingTotals.fuelFee.toLocaleString()}</span>
                    </div>
                  )}

                  {/* GPS */}
                  {bookingTotals.gpsFee > 0 && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 14px', borderBottom: `1px solid ${colors.lightGrey}` }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div style={{ width: '28px', height: '28px', borderRadius: '6px', backgroundColor: '#F3E5F5', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <Navigation size={14} color="#7B1FA2" />
                        </div>
                        <div>
                          <div style={{ fontSize: '13px', fontWeight: '600', color: colors.darkGrey }}>GPS Navigation</div>
                          <div style={{ fontSize: '11px', color: colors.mediumGrey }}>{bookingTotals.days} day{bookingTotals.days > 1 ? 's' : ''} × ₦1,000</div>
                        </div>
                      </div>
                      <span style={{ fontSize: '13px', fontWeight: '700', color: colors.darkGrey }}>₦{bookingTotals.gpsFee.toLocaleString()}</span>
                    </div>
                  )}

                  {/* VAT */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', backgroundColor: '#FAFAFA' }}>
                    <span style={{ fontSize: '12px', color: colors.mediumGrey }}>VAT (7.5%)</span>
                    <span style={{ fontSize: '12px', color: colors.mediumGrey }}>₦{bookingTotals.vat?.toLocaleString()}</span>
                  </div>
                </div>

                {/* Total */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 16px', marginTop: '12px', backgroundColor: `${colors.primary}10`, borderRadius: '12px', border: `2px solid ${colors.primary}` }}>
                  <span style={{ fontSize: '15px', fontWeight: '700', color: colors.darkGrey }}>Total Amount</span>
                  <span style={{ fontSize: '20px', fontWeight: '800', color: colors.primary }}>₦{bookingTotals.total?.toLocaleString()}</span>
                </div>
              </div>
            </div>

            <div style={{ textAlign: 'left', padding: '20px', backgroundColor: '#FFF3CD', borderRadius: '12px', marginBottom: '24px' }}>
              <h4 style={{ fontSize: '14px', fontWeight: '600', color: '#856404', margin: '0 0 8px 0' }}>Payment Instructions</h4>
              <p style={{ fontSize: '13px', color: '#856404', margin: 0 }}>
                Please transfer ₦{bookingTotals.total?.toLocaleString()} to:<br />
                <strong>C&I Leasing PLC</strong><br />
                Wema Bank - 0123456789<br />
                Use reference: {bookingReference}
              </p>
            </div>

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
              <button onClick={() => { setShowcaseView('browse'); setSelectedShowcaseVehicle(null); setClientBooking({ pickupDate: '', returnDate: '', withDriver: true, withInsurance: true, withFuel: true, withGPS: false, customerName: '', customerEmail: '', customerPhone: '', customerCompany: '', pickupLocation: '', returnLocation: '', pickupTime: '09:00', returnTime: '09:00', notes: '' }); }}
                style={{ padding: '14px 28px', backgroundColor: colors.primary, color: colors.white, border: 'none', borderRadius: '10px', fontSize: '15px', fontWeight: '600', cursor: 'pointer' }}>
                Book Another Vehicle
              </button>
            </div>
          </div>
        </div>
      );
    }

    return null;
  };

  // FLEET LIVE MAP VIEW
  const FleetLiveMapView = () => {
    // Lagos center coordinates
    const lagosCenter = [6.5244, 3.3792];

    return (
      <div style={{ padding: '32px' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <button
            onClick={() => setFleetSubView('list')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 20px',
              backgroundColor: colors.white,
              border: `1px solid ${colors.lightGrey}`,
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '600',
              color: colors.darkGrey,
            }}
          >
            <ChevronLeft size={18} />
            Back to Fleet
          </button>
          <h2 style={{ fontSize: '22px', fontWeight: '700', color: colors.darkGrey, margin: 0, display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Map size={24} color={colors.primary} />
            Live Fleet Map
          </h2>
          <div style={{ display: 'flex', gap: '12px' }}>
            <Button variant="ghost" icon={RefreshCw}>Refresh</Button>
            <Button variant="ghost" icon={Filter}>Filter</Button>
          </div>
        </div>

        {/* Map Container */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 350px', gap: '24px' }}>
          {/* Actual Leaflet Map */}
          <div style={{
            backgroundColor: colors.white,
            borderRadius: '16px',
            overflow: 'hidden',
            border: `1px solid ${colors.lightGrey}`,
            height: 'calc(100vh - 220px)',
            position: 'relative',
          }}>
            <MapContainer
              center={lagosCenter}
              zoom={12}
              style={{ height: '100%', width: '100%' }}
              scrollWheelZoom={true}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {fleetVehicles.map(vehicle => (
                <Marker
                  key={vehicle.id}
                  position={[vehicle.gps.latitude, vehicle.gps.longitude]}
                  icon={createVehicleIcon(vehicle.status, vehicle.gps.speed > 0)}
                >
                  <Popup>
                    <div style={{ minWidth: '200px' }}>
                      <div style={{ fontWeight: '700', fontSize: '14px', marginBottom: '4px', color: '#1A1A2E' }}>
                        {vehicle.name}
                      </div>
                      <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>
                        {vehicle.id} • {vehicle.registrationNo}
                      </div>
                      <div style={{
                        display: 'inline-block',
                        padding: '3px 8px',
                        borderRadius: '4px',
                        fontSize: '11px',
                        fontWeight: '600',
                        textTransform: 'uppercase',
                        backgroundColor: vehicle.status === 'active' ? '#D4EDDA' :
                                        vehicle.status === 'available' ? '#E9ECEF' :
                                        vehicle.status === 'booked' ? '#CCE5FF' :
                                        vehicle.status === 'maintenance' ? '#FFF3CD' : '#F8D7DA',
                        color: vehicle.status === 'active' ? '#155724' :
                               vehicle.status === 'available' ? '#495057' :
                               vehicle.status === 'booked' ? '#004085' :
                               vehicle.status === 'maintenance' ? '#856404' : '#721C24',
                        marginBottom: '8px'
                      }}>
                        {vehicle.status}
                      </div>
                      <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
                        📍 {vehicle.gps.address}
                      </div>
                      {vehicle.gps.speed > 0 && (
                        <div style={{ fontSize: '12px', color: '#28A745', marginBottom: '4px' }}>
                          🚗 Moving at {vehicle.gps.speed} km/h • Heading {vehicle.gps.heading}
                        </div>
                      )}
                      {vehicle.assignedDriver && (
                        <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
                          👤 Driver: {vehicle.assignedDriver}
                        </div>
                      )}
                      <div style={{ fontSize: '11px', color: '#999', marginTop: '8px' }}>
                        Last update: {new Date(vehicle.gps.lastUpdate).toLocaleString()}
                      </div>
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>

            {/* Map Legend */}
            <div style={{
              position: 'absolute',
              bottom: '20px',
              left: '20px',
              backgroundColor: colors.white,
              padding: '16px',
              borderRadius: '10px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
              zIndex: 1000,
            }}>
              <div style={{ fontSize: '12px', fontWeight: '600', marginBottom: '12px' }}>LEGEND</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {[
                  { color: '#28A745', label: 'Active (Moving)' },
                  { color: '#007BFF', label: 'Booked' },
                  { color: '#6C757D', label: 'Available (Parked)' },
                  { color: '#FFC107', label: 'Maintenance' },
                  { color: '#DC3545', label: 'Dormant' },
                ].map((item, idx) => (
                  <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px' }}>
                    <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: item.color, border: '2px solid white', boxShadow: '0 1px 3px rgba(0,0,0,0.3)' }} />
                    {item.label}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Vehicle List Panel */}
          <div style={{
            backgroundColor: colors.white,
            borderRadius: '16px',
            border: `1px solid ${colors.lightGrey}`,
            overflow: 'hidden',
          }}>
            <div style={{ padding: '16px', borderBottom: `1px solid ${colors.lightGrey}` }}>
              <h3 style={{ fontSize: '15px', fontWeight: '700', margin: 0, color: colors.darkGrey }}>
                Fleet Vehicles ({fleetVehicles.length})
              </h3>
            </div>
            <div style={{ maxHeight: 'calc(100vh - 310px)', overflowY: 'auto' }}>
              {fleetVehicles.map(vehicle => (
                <div
                  key={vehicle.id}
                  onClick={() => {
                    setSelectedVehicle(vehicle);
                    setFleetSubView('details');
                  }}
                  style={{
                    padding: '14px 16px',
                    borderBottom: `1px solid ${colors.lightGrey}`,
                    cursor: 'pointer',
                    transition: 'background-color 0.2s',
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#F8F9FA'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '6px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        backgroundColor: vehicle.gps.ignition ? colors.success : colors.mediumGrey,
                      }} />
                      <span style={{ fontSize: '11px', fontWeight: '700', color: colors.primary }}>{vehicle.id}</span>
                    </div>
                    <VehicleStatusBadge status={vehicle.status} />
                  </div>
                  <div style={{ fontSize: '14px', fontWeight: '600', color: colors.darkGrey, marginBottom: '4px' }}>
                    {vehicle.name}
                  </div>
                  <div style={{ fontSize: '12px', color: colors.mediumGrey, display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <MapPin size={11} />
                    {vehicle.gps.address}
                  </div>
                  {vehicle.gps.speed > 0 && (
                    <div style={{ fontSize: '11px', color: colors.success, marginTop: '4px' }}>
                      Moving at {vehicle.gps.speed} km/h • Heading {vehicle.gps.heading}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

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
          {currentView === 'fleet' && (
            <>
              {fleetSubView === 'list' && <FleetListView />}
              {fleetSubView === 'details' && <FleetVehicleDetailsView />}
              {fleetSubView === 'map' && <FleetLiveMapView />}
            </>
          )}
          {currentView === 'showcase' && <ShowcaseView />}
          {currentView !== 'bookings' && currentView !== 'fleet' && currentView !== 'showcase' && (
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
      <AddVehicleModal />
    </div>
  );
};

export default CNIFleetManagementUI;
