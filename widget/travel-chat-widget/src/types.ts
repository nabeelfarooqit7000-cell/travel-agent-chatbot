export type ChatFare = {
  rank: number;
  total_price: number;
  currency: string;
  validating_carrier?: string | null;
  cabin?: string | null;
  number_of_stops?: number | null;
  departure_airport?: string | null;
  arrival_airport?: string | null;
  departure_time?: string | null;
  arrival_time?: string | null;
  booking_link_hint?: string | null;
  raw_offer_id?: string | null;
};

export type ChatResponse = {
  answer: string;
  fares: ChatFare[];
  detected_trip?: {
    origin: string;
    destination: string;
    departure_date: string;
    return_date?: string | null;
    adults: number;
    children: number;
    infants: number;
    currency: string;
    max_results: number;
  } | null;
};

export type TravelChatWidgetLabels = {
  launcher?: string;
  title?: string;
  subtitle?: string;
  inputPlaceholder?: string;
  submit?: string;
  loading?: string;
  emptyState?: string;
  intro?: string;
};

export type TravelChatWidgetProps = {
  apiBaseUrl: string;
  className?: string;
  accentColor?: string;
  greeting?: string;
  labels?: TravelChatWidgetLabels;
  defaultOpen?: boolean;
  maxVisibleFares?: number;
  onFareSelect?: (fare: ChatFare) => void;
};
