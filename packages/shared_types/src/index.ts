export type ServiceName =
  | 'api_gateway'
  | 'identity_service'
  | 'ocr_service'
  | 'tax_service'
  | 'workflow_service'
  | 'notification_service';

export interface HealthResponse {
  status: 'ok';
  service: ServiceName;
}
