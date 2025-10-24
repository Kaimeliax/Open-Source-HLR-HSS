# HLR/HSS Web GUI Documentation

## Overview

The HLR/HSS Web GUI provides a user-friendly interface for managing and monitoring the HLR/HSS system. It offers comprehensive features for subscriber management, authentication testing, and system monitoring.

## Accessing the GUI

Once the HLR/HSS server is running, access the Web GUI by opening your browser and navigating to:

```
http://localhost:8080
```

Or if running on a remote server:
```
http://<server-ip>:8080
```

## Dashboard Sections

### 1. System Dashboard

The main dashboard provides an overview of the system status:

- **System Status**: Shows "Healthy" when the system is operational
- **Total Subscribers**: Displays the current number of registered subscribers
- **Active Sessions**: Shows the number of active OCS charging sessions
- **Roaming Partners**: Displays the count of configured roaming partners
- **System Information**: Shows HLR/HSS version, supported networks, interfaces, and authentication algorithms

The dashboard automatically refreshes every 30 seconds to provide real-time updates.

### 2. Subscriber Management

Manage subscribers with the following capabilities:

#### Add New Subscriber

Fill in the form with the following information:
- **IMSI** (required): International Mobile Subscriber Identity (15 digits)
- **MSISDN** (required): Mobile phone number
- **Ki** (required): Subscriber key (32 hexadecimal characters)
- **OPc** (required): Operator key (32 hexadecimal characters)
- **AMF**: Authentication Management Field (default: 8000)
- **Status**: Subscriber status (Service Granted, Operator Barring, Service Not Allowed)
- **Roaming Allowed**: Whether roaming is permitted (Yes/No)

Click "Add Subscriber" to create the new subscriber.

#### View Subscribers

The subscriber list displays:
- IMSI
- MSISDN
- Status (with color-coded badges)
- Roaming permission (Yes/No)
- Serving MME (if attached)
- Action buttons (View, Delete)

Click the refresh button to reload the subscriber list.

#### Delete Subscriber

Click the trash icon in the Actions column and confirm the deletion when prompted.

### 3. Authentication Testing

Test authentication vector generation:

1. Enter the IMSI of the subscriber
2. Click "Generate Vector"
3. View the authentication results including:
   - RAND (Random challenge)
   - AUTN (Authentication token)
   - XRES (Expected response)
   - KASME (Key for access security management)
   - CK (Cipher key)
   - IK (Integrity key)
   - AK (Anonymity key)
   - MAC_A (Message authentication code)

### 4. OCS Monitoring

View active Online Charging System sessions:

- Session ID
- IMSI
- Current Balance (in USD)
- Data Usage (formatted in B, KB, MB, GB, TB)

If OCS is not enabled, a message will be displayed indicating the service is unavailable.

### 5. Roaming Management

View configured roaming partners:

- PLMN ID (Public Land Mobile Network identifier)
- Partner Name
- Roaming Type (National/International)
- Agreement Status (Active/Inactive)

If roaming management is not enabled, a message will be displayed.

## Navigation

Use the top navigation bar to switch between different sections:
- **Dashboard** (🏠): System overview
- **Subscribers** (👥): Subscriber management
- **Authentication** (🔑): Auth vector testing
- **OCS** (💰): Charging session monitoring
- **Roaming** (🌐): Roaming partner management

## Notifications

The system displays toast notifications for:
- Successful operations (green)
- Errors (red)
- Warnings (yellow)
- Information (blue)

Notifications appear in the bottom-right corner and automatically dismiss after a few seconds.

## Keyboard Shortcuts

- Click navigation links to switch sections
- Use Tab to navigate between form fields
- Press Enter in text fields to submit forms

## Browser Compatibility

The Web GUI is compatible with modern browsers:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

JavaScript must be enabled for the GUI to function properly.

## Troubleshooting

### GUI Not Loading

1. Verify the HLR/HSS server is running
2. Check that port 8080 is accessible
3. Ensure no firewall is blocking the connection
4. Check browser console for JavaScript errors

### Data Not Updating

1. Check network connectivity
2. Verify the REST API is responding (check /health endpoint)
3. Refresh the page manually
4. Check browser console for API errors

### Forms Not Submitting

1. Ensure all required fields are filled
2. Verify data format (e.g., Ki and OPc must be 32 hex characters)
3. Check browser console for validation errors

## API Integration

The GUI communicates with the following REST API endpoints:

- `GET /health` - System health check
- `GET /api/v1/subscribers` - List subscribers
- `POST /api/v1/subscribers/{imsi}` - Create subscriber
- `GET /api/v1/subscribers/{imsi}` - Get subscriber details
- `DELETE /api/v1/subscribers/{imsi}` - Delete subscriber
- `POST /api/v1/auth/{imsi}` - Generate authentication vector
- `GET /api/v1/ocs/sessions` - List OCS sessions
- `GET /api/v1/ocs/sessions/{session_id}` - Get session details
- `GET /api/v1/roaming/partners` - List roaming partners

## Customization

### Changing the Port

Edit `config/config.yaml`:
```yaml
api:
  enabled: true
  bind_address: "0.0.0.0"
  port: 8080  # Change this value
  debug: false
```

### Styling

Custom styles can be modified in `hlr_hss/api/static/css/style.css`.

### Functionality

JavaScript functionality can be extended in `hlr_hss/api/static/js/app.js`.

## Security Considerations

1. **Authentication**: The current implementation does not include authentication. For production use, implement proper authentication and authorization.

2. **HTTPS**: Use HTTPS in production to encrypt communication between browser and server.

3. **Access Control**: Restrict access to the GUI using firewall rules or reverse proxy authentication.

4. **Input Validation**: The GUI includes client-side validation, but server-side validation is also enforced by the REST API.

## Performance

- The dashboard auto-refreshes every 30 seconds
- Large subscriber lists may require pagination (currently limited to 100)
- API responses are cached in the browser until the next refresh

## Support

For issues, questions, or feature requests:
- GitHub Issues: https://github.com/Kaimeliax/Open-Source-HLR-HSS/issues
- Documentation: See the main README.md file
