/**
 * Realistic logistics data matching backend models for ColdChain Sentinel command center.
 * Used for instant interactive demonstration and seamless offline/cold-start fallback.
 */

export interface ShipmentModel {
  id: string;
  tracking_number: string;
  medicine_name: string;
  batch_number: string;
  origin: string;
  origin_city: string;
  destination: string;
  destination_city: string;
  carrier_name: string;
  status: 'IN_TRANSIT' | 'VERIFIED' | 'FAILED' | 'REVIEW_REQUIRED';
  temp_status: 'SAFE' | 'WARNING' | 'BREACH';
  current_temp: number;
  min_allowed_temp: number;
  max_allowed_temp: number;
  max_excursion_seconds: number;
  payment_status: 'AUTHORIZED' | 'CAPTURED' | 'CAPTURE_BLOCKED' | 'HELD_FOR_REVIEW';
  payment_amount: number;
  currency: string;
  dispatched_at: string;
  estimated_arrival: string;
  progress_pct: number;
  waypoints: { name: string; lat: number; lng: number; status: 'completed' | 'active' | 'upcoming'; time?: string }[];
  current_location: { name: string; lat: number; lng: number };
  scenario_id?: string;
  description?: string;
}

export const DEMO_SHIPMENTS: ShipmentModel[] = [
  {
    id: 's-clean-01',
    tracking_number: 'CHALLENGE-01-CLEAN',
    medicine_name: 'Pfizer Comirnaty Bivalent mRNA',
    batch_number: 'LOT-CH-9921',
    origin: 'Basel Pharma Hub, Switzerland',
    origin_city: 'Basel',
    destination: "Guy's Hospital, London, UK",
    destination_city: 'London',
    carrier_name: 'Swiss WorldCargo',
    status: 'VERIFIED',
    temp_status: 'SAFE',
    current_temp: 4.8,
    min_allowed_temp: 2.0,
    max_allowed_temp: 8.0,
    max_excursion_seconds: 600,
    payment_status: 'CAPTURED',
    payment_amount: 12500,
    currency: 'USD',
    dispatched_at: '2026-11-10 08:00 UTC',
    estimated_arrival: 'Delivered (On Schedule)',
    progress_pct: 100,
    scenario_id: 'clean-shipment',
    description: 'Continuous cold storage strictly maintained within 2.0°C–8.0°C limits. 100% intact custody lineage. Compliance verified and payment capture auto-settled.',
    current_location: { name: "London Guy's Hospital", lat: 51.5048, lng: -0.0865 },
    waypoints: [
      { name: 'Basel Pharma Depot (Origin)', lat: 47.5596, lng: 7.5886, status: 'completed', time: '08:00' },
      { name: 'Zurich Airport Hub', lat: 47.4502, lng: 8.5619, status: 'completed', time: '10:30' },
      { name: 'London Heathrow Cargo Terminal', lat: 51.4700, lng: -0.4543, status: 'completed', time: '14:15' },
      { name: "Guy's Hospital London (Destination)", lat: 51.5048, lng: -0.0865, status: 'completed', time: '16:45' },
    ],
  },
  {
    id: 's-excursion-02',
    tracking_number: 'CHALLENGE-02-EXCURSION',
    medicine_name: 'Humira (Adalimumab) Syringes',
    batch_number: 'LOT-DE-4412',
    origin: 'Munich Biotech Center, Germany',
    origin_city: 'Munich',
    destination: 'Policlinico Umberto I, Rome, Italy',
    destination_city: 'Rome',
    carrier_name: 'Alitalia Cargo',
    status: 'FAILED',
    temp_status: 'BREACH',
    current_temp: 14.5,
    min_allowed_temp: 2.0,
    max_allowed_temp: 8.0,
    max_excursion_seconds: 600,
    payment_status: 'CAPTURE_BLOCKED',
    payment_amount: 8000,
    currency: 'USD',
    dispatched_at: '2026-11-10 09:30 UTC',
    estimated_arrival: 'Tarmac Hold (Quarantine)',
    progress_pct: 65,
    scenario_id: 'thermal-excursion',
    description: 'Temperature spiked to 14.5°C during airport tarmac transfer for 15 consecutive minutes (exceeding 10-minute limit). Verification rejected; payment capture blocked.',
    current_location: { name: 'Rome Fiumicino Cargo Tarmac', lat: 41.8003, lng: 12.2389 },
    waypoints: [
      { name: 'Munich Biotech Facility (Origin)', lat: 48.1351, lng: 11.5820, status: 'completed', time: '09:30' },
      { name: 'Munich Franz Josef Airport', lat: 48.3537, lng: 11.7750, status: 'completed', time: '11:15' },
      { name: 'Rome Fiumicino Tarmac (Excursion Point)', lat: 41.8003, lng: 12.2389, status: 'active', time: '14:20' },
      { name: 'Policlinico Umberto I Rome', lat: 41.9048, lng: 12.5134, status: 'upcoming' },
    ],
  },
  {
    id: 's-tamper-03',
    tracking_number: 'CHALLENGE-03-TAMPER',
    medicine_name: 'NovoRapid Insulin Vials',
    batch_number: 'LOT-DK-7703',
    origin: 'Copenhagen Biologics Hub, Denmark',
    origin_city: 'Copenhagen',
    destination: 'Karolinska University Hospital, Stockholm',
    destination_city: 'Stockholm',
    carrier_name: 'Nordic Express Cold',
    status: 'REVIEW_REQUIRED',
    temp_status: 'WARNING',
    current_temp: 5.4,
    min_allowed_temp: 2.0,
    max_allowed_temp: 8.0,
    max_excursion_seconds: 900,
    payment_status: 'HELD_FOR_REVIEW',
    payment_amount: 9500,
    currency: 'USD',
    dispatched_at: '2026-11-11 06:15 UTC',
    estimated_arrival: 'Withheld at Inspection',
    progress_pct: 80,
    scenario_id: 'evidence-tamper',
    description: 'Discrepancy detected between recorded evidence SHA-256 hash and physical telemetry payload. Fraud/tamper alert triggered; routed to QA investigation.',
    current_location: { name: 'Stockholm Arlanda Inspection Port', lat: 59.6498, lng: 17.9238 },
    waypoints: [
      { name: 'Copenhagen Facility (Origin)', lat: 55.6761, lng: 12.5683, status: 'completed', time: '06:15' },
      { name: 'Malmo Transit Center', lat: 55.6050, lng: 13.0038, status: 'completed', time: '09:00' },
      { name: 'Stockholm Arlanda Hub (Hash Mismatch)', lat: 59.6498, lng: 17.9238, status: 'active', time: '13:40' },
      { name: 'Karolinska Hospital Stockholm', lat: 59.3512, lng: 18.0345, status: 'upcoming' },
    ],
  },
  {
    id: 's-custody-04',
    tracking_number: 'CHALLENGE-04-CUSTODY',
    medicine_name: 'Keytruda (Pembrolizumab) Infusions',
    batch_number: 'LOT-KR-1209',
    origin: 'Seoul Central Biopharma, South Korea',
    origin_city: 'Seoul',
    destination: 'Todai Medical Hospital, Tokyo, Japan',
    destination_city: 'Tokyo',
    carrier_name: 'Trans-Asia Cold Express',
    status: 'REVIEW_REQUIRED',
    temp_status: 'SAFE',
    current_temp: 4.1,
    min_allowed_temp: 2.0,
    max_allowed_temp: 8.0,
    max_excursion_seconds: 600,
    payment_status: 'HELD_FOR_REVIEW',
    payment_amount: 11000,
    currency: 'USD',
    dispatched_at: '2026-11-11 04:00 UTC',
    estimated_arrival: 'Pending Airport Clearance Sign-off',
    progress_pct: 70,
    scenario_id: 'custody-gap',
    description: 'Missing mandatory airport cargo handover sign-off event in transit lineage. Incomplete custody chain forces compliance hold; automated payment release blocked.',
    current_location: { name: 'Tokyo Haneda Air Cargo Center', lat: 35.5494, lng: 139.7798 },
    waypoints: [
      { name: 'Seoul Biopharma Campus (Origin)', lat: 37.5665, lng: 126.9780, status: 'completed', time: '04:00' },
      { name: 'Incheon International Terminal', lat: 37.4602, lng: 126.4407, status: 'completed', time: '06:30' },
      { name: 'Tokyo Haneda Cargo (Missing Handover)', lat: 35.5494, lng: 139.7798, status: 'active', time: '11:00' },
      { name: 'Todai Hospital Tokyo', lat: 35.7128, lng: 139.7619, status: 'upcoming' },
    ],
  },
];

export const DEMO_TELEMETRY: Record<string, { time: string; temp: number; limit_min: number; limit_max: number }[]> = {
  'CHALLENGE-01-CLEAN': [
    { time: '08:00', temp: 4.2, limit_min: 2, limit_max: 8 },
    { time: '09:00', temp: 4.5, limit_min: 2, limit_max: 8 },
    { time: '10:00', temp: 4.8, limit_min: 2, limit_max: 8 },
    { time: '11:00', temp: 5.1, limit_min: 2, limit_max: 8 },
    { time: '12:00', temp: 4.9, limit_min: 2, limit_max: 8 },
    { time: '13:00', temp: 4.6, limit_min: 2, limit_max: 8 },
    { time: '14:00', temp: 5.3, limit_min: 2, limit_max: 8 },
    { time: '15:00', temp: 4.8, limit_min: 2, limit_max: 8 },
    { time: '16:00', temp: 4.4, limit_min: 2, limit_max: 8 },
    { time: '16:45', temp: 4.5, limit_min: 2, limit_max: 8 },
  ],
  'CHALLENGE-02-EXCURSION': [
    { time: '09:30', temp: 4.1, limit_min: 2, limit_max: 8 },
    { time: '10:30', temp: 4.6, limit_min: 2, limit_max: 8 },
    { time: '11:30', temp: 5.2, limit_min: 2, limit_max: 8 },
    { time: '12:30', temp: 7.8, limit_min: 2, limit_max: 8 },
    { time: '13:30', temp: 11.4, limit_min: 2, limit_max: 8 },
    { time: '14:00', temp: 13.8, limit_min: 2, limit_max: 8 },
    { time: '14:15', temp: 14.5, limit_min: 2, limit_max: 8 },
    { time: '14:30', temp: 14.0, limit_min: 2, limit_max: 8 },
    { time: '15:00', temp: 9.8, limit_min: 2, limit_max: 8 },
    { time: '16:00', temp: 6.2, limit_min: 2, limit_max: 8 },
  ],
  'CHALLENGE-03-TAMPER': [
    { time: '06:15', temp: 3.8, limit_min: 2, limit_max: 8 },
    { time: '08:00', temp: 4.2, limit_min: 2, limit_max: 8 },
    { time: '10:00', temp: 4.9, limit_min: 2, limit_max: 8 },
    { time: '12:00', temp: 5.1, limit_min: 2, limit_max: 8 },
    { time: '13:40', temp: 5.4, limit_min: 2, limit_max: 8 },
  ],
  'CHALLENGE-04-CUSTODY': [
    { time: '04:00', temp: 3.9, limit_min: 2, limit_max: 8 },
    { time: '06:00', temp: 4.0, limit_min: 2, limit_max: 8 },
    { time: '08:00', temp: 4.2, limit_min: 2, limit_max: 8 },
    { time: '10:00', temp: 4.4, limit_min: 2, limit_max: 8 },
    { time: '11:00', temp: 4.1, limit_min: 2, limit_max: 8 },
  ],
};

export const DEMO_EVIDENCE = [
  {
    id: 'ev-01',
    file_name: 'telemetry_log_swiss_cargo_01.csv',
    file_type: 'LOGGER_CSV',
    file_size: '148 KB',
    recorded_sha256: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    uploaded_at: '2026-11-10 16:50 UTC',
    uploaded_by: 'M. Blanc (Swiss Cargo Agent)',
    integrity_status: 'VERIFIED',
    shipment_tracking: 'CHALLENGE-01-CLEAN',
    status_label: 'Cryptographically Verified (Intact)',
  },
  {
    id: 'ev-02',
    file_name: 'nist_traceable_calibration_cert.pdf',
    file_type: 'CALIBRATION_CERTIFICATE',
    file_size: '2.4 MB',
    recorded_sha256: '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8',
    uploaded_at: '2026-11-10 07:45 UTC',
    uploaded_by: 'Dr. E. Vance (Chief Metrologist)',
    integrity_status: 'VERIFIED',
    shipment_tracking: 'CHALLENGE-01-CLEAN',
    status_label: 'Cryptographically Verified (Intact)',
  },
  {
    id: 'ev-03',
    file_name: 'alitalia_logger_tarmac_b2.csv',
    file_type: 'LOGGER_CSV',
    file_size: '112 KB',
    recorded_sha256: '4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a',
    uploaded_at: '2026-11-10 14:40 UTC',
    uploaded_by: 'G. Rossi (Ground Handler)',
    integrity_status: 'VERIFIED',
    shipment_tracking: 'CHALLENGE-02-EXCURSION',
    status_label: 'Breach Detected: Excursion > 10m',
  },
  {
    id: 'ev-04',
    file_name: 'tampered_telemetry_payload.csv',
    file_type: 'LOGGER_CSV',
    file_size: '98 KB',
    recorded_sha256: '3a493a7a9a1d3f9b2c8a14b09b5531fcacdabf8a4b227777d4dd1fc61c6f884f',
    uploaded_at: '2026-11-11 13:45 UTC',
    uploaded_by: 'Third-party Logistics Operator',
    integrity_status: 'HASH_MISMATCH',
    shipment_tracking: 'CHALLENGE-03-TAMPER',
    status_label: 'TAMPER DETECTED: Hash Mismatch',
  },
];

export const DEMO_CARRIERS = [
  {
    name: 'Swiss WorldCargo',
    fleet_type: 'Air Freight / Active Containers',
    total_shipments: 142,
    success_rate: 99.3,
    avg_temp_variance: 0.3,
    grade: 'A+',
    incidents: 0,
    compliance_score: 98.7,
  },
  {
    name: 'Lufthansa Cargo Life/Fresh',
    fleet_type: 'Air Cargo Cold Pods',
    total_shipments: 118,
    success_rate: 98.2,
    avg_temp_variance: 0.5,
    grade: 'A',
    incidents: 1,
    compliance_score: 96.1,
  },
  {
    name: 'Nordic Express Cold',
    fleet_type: 'Refrigerated Road Freight',
    total_shipments: 64,
    success_rate: 95.3,
    avg_temp_variance: 0.8,
    grade: 'B+',
    incidents: 2,
    compliance_score: 91.4,
  },
  {
    name: 'Alitalia Cargo',
    fleet_type: 'Air Cargo Tarmac Transfers',
    total_shipments: 47,
    success_rate: 82.9,
    avg_temp_variance: 2.4,
    grade: 'F (Breach)',
    incidents: 5,
    compliance_score: 74.2,
  },
];

export const DEMO_INVESTIGATIONS = [
  {
    id: 'INV-2026-001',
    shipment_tracking: 'CHALLENGE-02-EXCURSION',
    priority: 'CRITICAL',
    title: 'Severe Tarmac Temperature Spike (14.5°C Breach)',
    category: 'THERMAL_EXCURSION',
    status: 'IN_REVIEW',
    opened_at: '2026-11-10 14:35 UTC',
    assigned_to: 'Sarah Jenkins (QA Specialist)',
    findings: 'Thermal breach identified during Rome Fiumicino tarmac transfer. Sensor recorded 14.5°C for 15 minutes, surpassing the 10-minute allowed excursion threshold. Product viability compromised; payment capture halted.',
  },
  {
    id: 'INV-2026-002',
    shipment_tracking: 'CHALLENGE-03-TAMPER',
    priority: 'HIGH',
    title: 'Cryptographic SHA-256 Digest Mismatch in Telemetry File',
    category: 'EVIDENCE_TAMPER',
    status: 'OPEN',
    opened_at: '2026-11-11 13:50 UTC',
    assigned_to: 'Alex Rivera (Security & Compliance Auditor)',
    findings: 'Physical telemetry CSV payload computed SHA-256 does not match recorded digest. Discrepancy indicates external modification post-signing. Shipment quarantined pending cryptographic root analysis.',
  },
  {
    id: 'INV-2026-003',
    shipment_tracking: 'CHALLENGE-04-CUSTODY',
    priority: 'MEDIUM',
    title: 'Chain of Custody Discontinuity at Haneda Airport',
    category: 'CUSTODY_GAP',
    status: 'IN_REVIEW',
    opened_at: '2026-11-11 11:15 UTC',
    assigned_to: 'Kenji Takahashi (Operations Auditor)',
    findings: 'Missing mandatory physical handover log between international air carrier and airport warehouse custodian. Incomplete chain of custody triggers automated payment escrow block.',
  },
];
