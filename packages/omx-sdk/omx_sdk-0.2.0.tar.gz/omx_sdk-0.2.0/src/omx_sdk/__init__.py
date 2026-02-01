"""OMX SDK for Python - Official SDK for Oxinion Marketing Exchange."""

import os
from typing import Optional, Dict, Any, List, Union
import httpx


# ==================== Data Models ====================

class Location:
    """Location model for geofencing."""
    def __init__(self, lat: float, lng: float):
        self.lat = lat
        self.lng = lng


class GeoFence:
    """Geofence model."""
    def __init__(self, id: str, name: str, location: Dict[str, float], radius: int, events: List[str], created_at: str):
        self.id = id
        self.name = name
        self.location = location
        self.radius = radius
        self.events = events
        self.created_at = created_at


class NotificationResult:
    """Notification result model."""
    def __init__(self, message_id: str, status: str):
        self.message_id = message_id
        self.status = status


class EmailResult:
    """Email result model."""
    def __init__(self, message_id: str, status: str):
        self.message_id = message_id
        self.status = status


class EmailCampaign:
    """Email campaign model."""
    def __init__(self, id: str, name: str, subject: str, status: str):
        self.id = id
        self.name = name
        self.subject = subject
        self.status = status


class EmailTemplate:
    """Email template model."""
    def __init__(self, id: str, name: str, subject: str):
        self.id = id
        self.name = name
        self.subject = subject


class Beacon:
    """Beacon model."""
    def __init__(self, id: str, uuid: str, major: int, minor: int, name: str, location: Optional[Dict[str, Any]] = None):
        self.id = id
        self.uuid = uuid
        self.major = major
        self.minor = minor
        self.name = name
        self.location = location


class Webhook:
    """Webhook model."""
    def __init__(self, id: str, url: str, events: List[str], active: bool):
        self.id = id
        self.url = url
        self.events = events
        self.active = active


class Campaign:
    """Campaign model."""
    def __init__(self, id: str, name: str, description: str, channels: List[str], status: str):
        self.id = id
        self.name = name
        self.description = description
        self.channels = channels
        self.status = status


class NotificationHistory:
    """Notification history model."""
    def __init__(self, items: List[Dict[str, Any]], total: int):
        self.items = items
        self.total = total


class NotificationStatus:
    """Notification status model."""
    def __init__(self, notification_id: str, status: str, delivered_at: Optional[str] = None):
        self.notification_id = notification_id
        self.status = status
        self.delivered_at = delivered_at


class GeoEvent:
    """Geo event model."""
    def __init__(self, id: str, geofence_id: str, event_type: str, user_id: str, timestamp: str):
        self.id = id
        self.geofence_id = geofence_id
        self.event_type = event_type
        self.user_id = user_id
        self.timestamp = timestamp


class WebhookDelivery:
    """Webhook delivery model."""
    def __init__(self, id: str, webhook_id: str, status: str, timestamp: str):
        self.id = id
        self.webhook_id = webhook_id
        self.status = status
        self.timestamp = timestamp


# ==================== Data Models ====================

class Workflow:
    """Workflow model."""
    def __init__(self, id: str, name: str, description: str, status: str, created_at: str):
        self.id = id
        self.name = name
        self.description = description
        self.status = status
        self.created_at = created_at


class Segment:
    """Segment model."""
    def __init__(self, id: str, name: str, description: str, criteria: Dict[str, Any], user_count: int):
        self.id = id
        self.name = name
        self.description = description
        self.criteria = criteria
        self.user_count = user_count


class Event:
    """Event model."""
    def __init__(self, id: str, user_id: str, event_type: str, data: Dict[str, Any], timestamp: str):
        self.id = id
        self.user_id = user_id
        self.event_type = event_type
        self.data = data
        self.timestamp = timestamp


class AnalyticsData:
    """Analytics data model."""
    def __init__(self, metrics: Dict[str, Any], time_range: Dict[str, str]):
        self.metrics = metrics
        self.time_range = time_range


# ==================== Module Managers ====================

class NotificationManager:
    """Notification module for sending push notifications."""

    def __init__(self, client: 'OMXClient'):
        self.client = client

    async def send(
        self,
        title: str,
        message: str,
        recipients: List[str],
        data: Optional[Dict[str, Any]] = None,
        deep_link: Optional[str] = None
    ) -> NotificationResult:
        """Send push notification using keyword arguments (Pythonic style).

        Args:
            title: Notification title
            message: Notification message body
            recipients: List of user IDs or device tokens
            data: Optional custom data payload
            deep_link: Optional deep link URL

        Returns:
            NotificationResult with message_id and status
        """
        payload = {
            "title": title,
            "message": message,
            "recipients": recipients
        }
        if data:
            payload["data"] = data
        if deep_link:
            payload["deepLink"] = deep_link

        response = await self.client._make_request('POST', '/notifications/send', payload)
        return NotificationResult(
            message_id=response['messageId'],
            status=response['status']
        )

    async def send_to_segment(
        self,
        title: str,
        message: str,
        segment: str,
        data: Optional[Dict[str, Any]] = None,
        deep_link: Optional[str] = None
    ) -> NotificationResult:
        """Send notification to audience segment.

        Args:
            title: Notification title
            message: Notification message body
            segment: Segment identifier
            data: Optional custom data payload
            deep_link: Optional deep link URL

        Returns:
            NotificationResult with message_id and status
        """
        payload = {
            "title": title,
            "message": message,
            "segment": segment
        }
        if data:
            payload["data"] = data
        if deep_link:
            payload["deepLink"] = deep_link

        response = await self.client._make_request('POST', '/notifications/segment', payload)
        return NotificationResult(
            message_id=response['messageId'],
            status=response['status']
        )

    async def get_history(
        self,
        limit: Optional[int] = 50,
        status: Optional[str] = None
    ) -> NotificationHistory:
        """Get notification history.

        Args:
            limit: Maximum number of records to return
            status: Filter by status (delivered, failed, etc.)

        Returns:
            NotificationHistory with items and total count
        """
        params = {"limit": str(limit)}
        if status:
            params["status"] = status

        response = await self.client._make_request('GET', '/notifications/history', params=params)
        return NotificationHistory(
            items=response.get('items', []),
            total=response.get('total', 0)
        )

    async def get_status(self, notification_id: str) -> NotificationStatus:
        """Check notification status.

        Args:
            notification_id: Notification ID to check

        Returns:
            NotificationStatus with current status
        """
        response = await self.client._make_request('GET', f'/notifications/{notification_id}/status')
        return NotificationStatus(
            notification_id=response['notificationId'],
            status=response['status'],
            delivered_at=response.get('deliveredAt')
        )


class EmailManager:
    """Email module for transactional emails and email campaigns."""

    def __init__(self, client: 'OMXClient'):
        self.client = client

    async def send(
        self,
        to: str,
        subject: str,
        template: str,
        variables: Optional[Dict[str, Any]] = None,
        html: Optional[str] = None
    ) -> EmailResult:
        """Send transactional email using keyword arguments (Pythonic style).

        Args:
            to: Recipient email address
            subject: Email subject line
            template: Template name to use
            variables: Template variables
            html: Optional raw HTML content

        Returns:
            EmailResult with message_id and status
        """
        payload = {
            "to": to,
            "subject": subject,
            "template": template
        }
        if variables:
            payload["variables"] = variables
        if html:
            payload["html"] = html

        response = await self.client._make_request('POST', '/email/send', payload)
        return EmailResult(
            message_id=response['messageId'],
            status=response['status']
        )

    async def create_campaign(
        self,
        name: str,
        subject: str,
        template: str,
        recipients: List[str],
        scheduled_at: Optional[str] = None
    ) -> EmailCampaign:
        """Create email-only campaign.

        Args:
            name: Campaign name
            subject: Email subject line
            template: Template name to use
            recipients: List of recipient email addresses or segments
            scheduled_at: Optional scheduled send time (ISO 8601)

        Returns:
            EmailCampaign object
        """
        payload = {
            "name": name,
            "subject": subject,
            "template": template,
            "recipients": recipients
        }
        if scheduled_at:
            payload["scheduledAt"] = scheduled_at

        response = await self.client._make_request('POST', '/email/campaigns', payload)
        return EmailCampaign(
            id=response['id'],
            name=response['name'],
            subject=response['subject'],
            status=response['status']
        )

    async def send_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Send email campaign.

        Args:
            campaign_id: Campaign ID to send

        Returns:
            Campaign send result
        """
        return await self.client._make_request('POST', f'/email/campaigns/{campaign_id}/send')

    async def create_template(
        self,
        name: str,
        subject: str,
        html: str,
        variables: Optional[List[str]] = None
    ) -> EmailTemplate:
        """Create email template.

        Args:
            name: Template name
            subject: Email subject line with optional variables
            html: HTML content with variable placeholders
            variables: List of variable names used in template

        Returns:
            EmailTemplate object
        """
        payload = {
            "name": name,
            "subject": subject,
            "html": html
        }
        if variables:
            payload["variables"] = variables

        response = await self.client._make_request('POST', '/email/templates', payload)
        return EmailTemplate(
            id=response['id'],
            name=response['name'],
            subject=response['subject']
        )


class GeoTriggerManager:
    """GeoTrigger module for location-based automation."""

    def __init__(self, client: 'OMXClient'):
        self.client = client

    async def create(
        self,
        name: str,
        location: Dict[str, float],
        radius: int,
        events: List[str]
    ) -> GeoFence:
        """Create circular geofence using keyword arguments (Pythonic style).

        Args:
            name: Geofence name
            location: Location dict with lat and lng keys
            radius: Radius in meters
            events: List of events to track (enter, exit, dwell)

        Returns:
            GeoFence object
        """
        payload = {
            "name": name,
            "location": location,
            "radius": radius,
            "events": events
        }

        response = await self.client._make_request('POST', '/geotriggers', payload)
        return GeoFence(
            id=response['id'],
            name=response['name'],
            location=response['location'],
            radius=response['radius'],
            events=response['events'],
            created_at=response['createdAt']
        )

    async def create_polygon_fence(
        self,
        name: str,
        coordinates: List[List[float]],
        events: List[str]
    ) -> GeoFence:
        """Create polygon geofence.

        Args:
            name: Geofence name
            coordinates: List of [lat, lng] coordinate pairs
            events: List of events to track

        Returns:
            GeoFence object
        """
        payload = {
            "name": name,
            "coordinates": coordinates,
            "events": events,
            "type": "polygon"
        }

        response = await self.client._make_request('POST', '/geotriggers', payload)
        return GeoFence(
            id=response['id'],
            name=response['name'],
            location=response.get('location', {}),
            radius=response.get('radius', 0),
            events=response['events'],
            created_at=response['createdAt']
        )

    async def get_geofences(
        self,
        active: Optional[bool] = None,
        near: Optional[Dict[str, Any]] = None
    ) -> List[GeoFence]:
        """Get active geofences.

        Args:
            active: Filter by active status
            near: Filter by proximity (dict with lat, lng, radius)

        Returns:
            List of GeoFence objects
        """
        params = {}
        if active is not None:
            params["active"] = str(active).lower()
        if near:
            params["near"] = f"{near['lat']},{near['lng']},{near['radius']}"

        response = await self.client._make_request('GET', '/geotriggers', params=params)
        return [
            GeoFence(
                id=item['id'],
                name=item['name'],
                location=item['location'],
                radius=item['radius'],
                events=item['events'],
                created_at=item['createdAt']
            )
            for item in response
        ]

    async def check_location(
        self,
        geofence_id: str,
        latitude: float,
        longitude: float
    ) -> bool:
        """Check if location is inside geofence.

        Args:
            geofence_id: Geofence ID to check
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            True if inside geofence, False otherwise
        """
        params = {
            "lat": str(latitude),
            "lng": str(longitude)
        }
        response = await self.client._make_request('GET', f'/geotriggers/{geofence_id}/check', params=params)
        return response.get('isInside', False)

    async def get_events(
        self,
        geofence_id: str,
        event_type: Optional[str] = None,
        since: Optional[str] = None
    ) -> List[GeoEvent]:
        """Get location events.

        Args:
            geofence_id: Geofence ID
            event_type: Filter by event type (enter, exit, dwell)
            since: Filter by timestamp (ISO 8601)

        Returns:
            List of GeoEvent objects
        """
        params = {}
        if event_type:
            params["eventType"] = event_type
        if since:
            params["since"] = since

        response = await self.client._make_request('GET', f'/geotriggers/{geofence_id}/events', params=params)
        return [
            GeoEvent(
                id=item['id'],
                geofence_id=item['geofenceId'],
                event_type=item['eventType'],
                user_id=item['userId'],
                timestamp=item['timestamp']
            )
            for item in response
        ]

    async def update_geofence(
        self,
        geofence_id: str,
        name: Optional[str] = None,
        radius: Optional[int] = None,
        events: Optional[List[str]] = None
    ) -> GeoFence:
        """Update geofence.

        Args:
            geofence_id: Geofence ID to update
            name: Optional new name
            radius: Optional new radius
            events: Optional new events list

        Returns:
            Updated GeoFence object
        """
        payload = {}
        if name:
            payload["name"] = name
        if radius:
            payload["radius"] = radius
        if events:
            payload["events"] = events

        response = await self.client._make_request('PUT', f'/geotriggers/{geofence_id}', payload)
        return GeoFence(
            id=response['id'],
            name=response['name'],
            location=response['location'],
            radius=response['radius'],
            events=response['events'],
            created_at=response['createdAt']
        )

    async def remove_geofence(self, geofence_id: str) -> None:
        """Remove geofence.

        Args:
            geofence_id: Geofence ID to remove
        """
        await self.client._make_request('DELETE', f'/geotriggers/{geofence_id}')

    async def remove_multiple_geofences(self, geofence_ids: List[str]) -> None:
        """Bulk remove geofences.

        Args:
            geofence_ids: List of geofence IDs to remove
        """
        payload = {"ids": geofence_ids}
        await self.client._make_request('POST', '/geotriggers/bulk-delete', payload)


class BeaconManager:
    """Beacon module for Bluetooth beacon management."""

    def __init__(self, client: 'OMXClient'):
        self.client = client

    async def register(
        self,
        uuid: str,
        major: int,
        minor: int,
        name: str,
        location: Optional[Dict[str, Any]] = None
    ) -> Beacon:
        """Register new beacon using keyword arguments (Pythonic style).

        Args:
            uuid: Beacon UUID
            major: Major value
            minor: Minor value
            name: Beacon name
            location: Optional location data (latitude, longitude, description)

        Returns:
            Beacon object
        """
        payload = {
            "uuid": uuid,
            "major": major,
            "minor": minor,
            "name": name
        }
        if location:
            payload["location"] = location

        response = await self.client._make_request('POST', '/beacons', payload)
        return Beacon(
            id=response['id'],
            uuid=response['uuid'],
            major=response['major'],
            minor=response['minor'],
            name=response['name'],
            location=response.get('location')
        )

    async def get_nearby(
        self,
        latitude: float,
        longitude: float,
        radius: int
    ) -> List[Beacon]:
        """Get nearby beacons.

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius: Search radius in meters

        Returns:
            List of Beacon objects
        """
        params = {
            "lat": str(latitude),
            "lng": str(longitude),
            "radius": str(radius)
        }

        response = await self.client._make_request('GET', '/beacons/nearby', params=params)
        return [
            Beacon(
                id=item['id'],
                uuid=item['uuid'],
                major=item['major'],
                minor=item['minor'],
                name=item['name'],
                location=item.get('location')
            )
            for item in response
        ]

    async def update_config(
        self,
        beacon_id: str,
        transmission_power: Optional[int] = None,
        advertising_interval: Optional[int] = None,
        name: Optional[str] = None
    ) -> Beacon:
        """Update beacon configuration.

        Args:
            beacon_id: Beacon ID to update
            transmission_power: Optional transmission power in dBm
            advertising_interval: Optional advertising interval in ms
            name: Optional new name

        Returns:
            Updated Beacon object
        """
        payload = {}
        if transmission_power is not None:
            payload["transmissionPower"] = transmission_power
        if advertising_interval is not None:
            payload["advertisingInterval"] = advertising_interval
        if name:
            payload["name"] = name

        response = await self.client._make_request('PUT', f'/beacons/{beacon_id}', payload)
        return Beacon(
            id=response['id'],
            uuid=response['uuid'],
            major=response['major'],
            minor=response['minor'],
            name=response['name'],
            location=response.get('location')
        )

    async def get_status(self, beacon_id: str) -> Dict[str, Any]:
        """Check beacon status.

        Args:
            beacon_id: Beacon ID to check

        Returns:
            Beacon status information
        """
        return await self.client._make_request('GET', f'/beacons/{beacon_id}/status')


class WebhookManager:
    """Webhook module for real-time event notifications."""

    def __init__(self, client: 'OMXClient'):
        self.client = client

    async def create(
        self,
        url: str,
        events: List[str],
        secret: Optional[str] = None,
        active: bool = True
    ) -> Webhook:
        """Create webhook endpoint using keyword arguments (Pythonic style).

        Args:
            url: Webhook endpoint URL
            events: List of events to subscribe to
            secret: Optional webhook secret for signature verification
            active: Whether webhook is active

        Returns:
            Webhook object
        """
        payload = {
            "url": url,
            "events": events,
            "active": active
        }
        if secret:
            payload["secret"] = secret

        response = await self.client._make_request('POST', '/webhooks', payload)
        return Webhook(
            id=response['id'],
            url=response['url'],
            events=response['events'],
            active=response['active']
        )

    async def update(
        self,
        webhook_id: str,
        events: Optional[List[str]] = None,
        retry_policy: Optional[Dict[str, Any]] = None,
        active: Optional[bool] = None
    ) -> Webhook:
        """Update webhook configuration.

        Args:
            webhook_id: Webhook ID to update
            events: Optional new events list
            retry_policy: Optional retry policy configuration
            active: Optional active status

        Returns:
            Updated Webhook object
        """
        payload = {}
        if events:
            payload["events"] = events
        if retry_policy:
            payload["retryPolicy"] = retry_policy
        if active is not None:
            payload["active"] = active

        response = await self.client._make_request('PUT', f'/webhooks/{webhook_id}', payload)
        return Webhook(
            id=response['id'],
            url=response['url'],
            events=response['events'],
            active=response['active']
        )

    async def get_deliveries(
        self,
        webhook_id: str,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[WebhookDelivery]:
        """Get webhook delivery logs.

        Args:
            webhook_id: Webhook ID
            status: Filter by status (success, failed)
            limit: Maximum number of records

        Returns:
            List of WebhookDelivery objects
        """
        params = {"limit": str(limit)}
        if status:
            params["status"] = status

        response = await self.client._make_request('GET', f'/webhooks/{webhook_id}/deliveries', params=params)
        return [
            WebhookDelivery(
                id=item['id'],
                webhook_id=item['webhookId'],
                status=item['status'],
                timestamp=item['timestamp']
            )
            for item in response
        ]

    async def retry(self, delivery_id: str) -> Dict[str, Any]:
        """Retry failed delivery.

        Args:
            delivery_id: Delivery ID to retry

        Returns:
            Retry result
        """
        return await self.client._make_request('POST', f'/webhooks/deliveries/{delivery_id}/retry')

    async def list(self, active: Optional[bool] = None) -> List[Webhook]:
        """Get all webhooks.

        Args:
            active: Filter by active status

        Returns:
            List of Webhook objects
        """
        params = {}
        if active is not None:
            params["active"] = str(active).lower()

        response = await self.client._make_request('GET', '/webhooks', params=params)
        return [
            Webhook(
                id=item['id'],
                url=item['url'],
                events=item['events'],
                active=item['active']
            )
            for item in response
        ]


class CampaignManager:
    """Campaign module for multi-channel marketing campaigns."""

    def __init__(self, client: 'OMXClient'):
        self.client = client

    async def create(
        self,
        name: str,
        description: str,
        channels: List[str],
        schedule: Optional[Dict[str, str]] = None,
        targeting: Optional[Dict[str, Any]] = None
    ) -> Campaign:
        """Create marketing campaign using keyword arguments (Pythonic style).

        Args:
            name: Campaign name
            description: Campaign description
            channels: List of channels (email, push_notification, webhook)
            schedule: Optional schedule with start_date and end_date
            targeting: Optional targeting configuration (segments, geofences)

        Returns:
            Campaign object
        """
        payload = {
            "name": name,
            "description": description,
            "channels": channels
        }
        if schedule:
            payload["schedule"] = schedule
        if targeting:
            payload["targeting"] = targeting

        response = await self.client._make_request('POST', '/campaigns', payload)
        return Campaign(
            id=response['id'],
            name=response['name'],
            description=response['description'],
            channels=response['channels'],
            status=response['status']
        )

    async def update(
        self,
        campaign_id: str,
        status: Optional[str] = None,
        budget: Optional[Dict[str, Any]] = None
    ) -> Campaign:
        """Update campaign settings.

        Args:
            campaign_id: Campaign ID to update
            status: Optional new status
            budget: Optional budget configuration

        Returns:
            Updated Campaign object
        """
        payload = {}
        if status:
            payload["status"] = status
        if budget:
            payload["budget"] = budget

        response = await self.client._make_request('PUT', f'/campaigns/{campaign_id}', payload)
        return Campaign(
            id=response['id'],
            name=response['name'],
            description=response['description'],
            channels=response['channels'],
            status=response['status']
        )

    async def pause(self, campaign_id: str) -> None:
        """Pause campaign.

        Args:
            campaign_id: Campaign ID to pause
        """
        await self.client._make_request('POST', f'/campaigns/{campaign_id}/pause')

    async def resume(self, campaign_id: str) -> None:
        """Resume campaign.

        Args:
            campaign_id: Campaign ID to resume
        """
        await self.client._make_request('POST', f'/campaigns/{campaign_id}/resume')

    async def execute(
        self,
        campaign_id: str,
        trigger_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute multi-channel campaign.

        Args:
            campaign_id: Campaign ID to execute
            trigger_data: Optional trigger data (user_id, location, etc.)

        Returns:
            Execution result
        """
        payload = trigger_data or {}
        return await self.client._make_request('POST', f'/campaigns/{campaign_id}/execute', payload)

    async def list(
        self,
        status: Optional[str] = None,
        sort_by: Optional[str] = None,
        limit: int = 20
    ) -> List[Campaign]:
        """Get all campaigns.

        Args:
            status: Filter by status
            sort_by: Sort field (created_date, name, etc.)
            limit: Maximum number of records

        Returns:
            List of Campaign objects
        """
        params = {"limit": str(limit)}
        if status:
            params["status"] = status
        if sort_by:
            params["sortBy"] = sort_by

        response = await self.client._make_request('GET', '/campaigns', params=params)
        return [
            Campaign(
                id=item['id'],
                name=item['name'],
                description=item.get('description', ''),
                channels=item['channels'],
                status=item['status']
            )
            for item in response
        ]


class WorkflowManager:
    """Workflow module for visual workflow automation."""

    def __init__(self, client: 'OMXClient'):
        self.client = client

    async def create_workflow(
        self,
        name: str,
        description: str,
        config: Dict[str, Any]
    ) -> Workflow:
        """Create visual workflow using keyword arguments.

        Args:
            name: Workflow name
            description: Workflow description  
            config: Workflow configuration (triggers, actions, conditions)

        Returns:
            Workflow object
        """
        payload = {
            "name": name,
            "description": description,
            "config": config
        }

        response = await self.client._make_request('POST', '/workflows', payload)
        return Workflow(
            id=response['id'],
            name=response['name'],
            description=response['description'],
            status=response['status'],
            created_at=response['createdAt']
        )

    async def run_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute workflow.

        Args:
            workflow_id: Workflow ID to execute

        Returns:
            Execution result
        """
        return await self.client._make_request('POST', f'/workflows/{workflow_id}/execute')

    async def list(self, status: Optional[str] = None) -> List[Workflow]:
        """Get all workflows.

        Args:
            status: Filter by status (active, paused, draft)

        Returns:
            List of Workflow objects
        """
        params = {}
        if status:
            params["status"] = status

        response = await self.client._make_request('GET', '/workflows', params=params)
        return [
            Workflow(
                id=item['id'],
                name=item['name'],
                description=item['description'],
                status=item['status'],
                created_at=item['createdAt']
            )
            for item in response
        ]


class AnalyticsManager:
    """Analytics module for data insights and reporting."""

    def __init__(self, client: 'OMXClient'):
        self.client = client

    async def get_geotrigger_stats(
        self,
        geotrigger_id: str,
        time_range: Optional[str] = None
    ) -> AnalyticsData:
        """Get geotrigger analytics.

        Args:
            geotrigger_id: Geotrigger ID
            time_range: Time range filter (7d, 30d, 90d)

        Returns:
            AnalyticsData with metrics
        """
        params = {"geoTriggerId": geotrigger_id}
        if time_range:
            params["timeRange"] = time_range

        response = await self.client._make_request('GET', '/analytics/geotriggers', params=params)
        return AnalyticsData(
            metrics=response.get('metrics', {}),
            time_range=response.get('timeRange', {})
        )


class SegmentManager:
    """Segment module for audience segmentation."""

    def __init__(self, client: 'OMXClient'):
        self.client = client

    async def create_segment(
        self,
        name: str,
        description: str,
        criteria: Dict[str, Any]
    ) -> Segment:
        """Create audience segment.

        Args:
            name: Segment name
            description: Segment description
            criteria: Segmentation criteria (location, behavior, attributes)

        Returns:
            Segment object
        """
        payload = {
            "name": name,
            "description": description,
            "criteria": criteria
        }

        response = await self.client._make_request('POST', '/segments', payload)
        return Segment(
            id=response['id'],
            name=response['name'],
            description=response['description'],
            criteria=response['criteria'],
            user_count=response.get('userCount', 0)
        )

    async def get_segment_users(self, segment_id: str) -> List[Dict[str, Any]]:
        """Get users in segment.

        Args:
            segment_id: Segment ID

        Returns:
            List of user objects
        """
        return await self.client._make_request('GET', f'/segments/{segment_id}/users')

    async def list(self, active: Optional[bool] = None) -> List[Segment]:
        """Get all segments.

        Args:
            active: Filter by active status

        Returns:
            List of Segment objects
        """
        params = {}
        if active is not None:
            params["active"] = str(active).lower()

        response = await self.client._make_request('GET', '/segments', params=params)
        return [
            Segment(
                id=item['id'],
                name=item['name'],
                description=item['description'],
                criteria=item['criteria'],
                user_count=item.get('userCount', 0)
            )
            for item in response
        ]


class EventsManager:
    """Events module for tracking user interactions and behaviors."""

    def __init__(self, client: 'OMXClient'):
        self.client = client

    async def track_event(
        self,
        user_id: str,
        event_type: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track user event.

        Args:
            user_id: User identifier
            event_type: Type of event (page_view, purchase, etc.)
            data: Optional event data payload
        """
        payload = {
            "userId": user_id,
            "eventType": event_type
        }
        if data:
            payload["data"] = data

        await self.client._make_request('POST', '/events', payload)

    async def get_event_timeline(
        self,
        user_id: str,
        limit: Optional[int] = 50
    ) -> List[Event]:
        """Get user event timeline.

        Args:
            user_id: User identifier
            limit: Maximum number of events

        Returns:
            List of Event objects
        """
        params = {"userId": user_id}
        if limit:
            params["limit"] = str(limit)

        response = await self.client._make_request('GET', '/events/timeline', params=params)
        return [
            Event(
                id=item['id'],
                user_id=item['userId'],
                event_type=item['eventType'],
                data=item.get('data', {}),
                timestamp=item['timestamp']
            )
            for item in response
        ]


# ==================== Main Client ====================

class OMXClient:
    """Main OMX SDK client.

    The foundation module that provides authentication and access to all OMX SDK features.
    Supports async context manager for automatic cleanup.

    Example:
        ```python
        # Recommended: Use async context manager
        async with OMXClient(
            client_id="your_client_id",
            secret_key="your_secret_key"
        ) as omx:
            # Your code here - authentication handled automatically
            pass

        # Alternative: Manual initialization
        omx = OMXClient(
            client_id="your_client_id",
            secret_key="your_secret_key"
        )
        # ... your code ...
        await omx.close()  # Don't forget to close!
        ```
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        secret_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """Initialize the OMX client.

        Args:
            client_id: OMX client ID (can also be set via OMX_CLIENT_ID env var)
            secret_key: OMX secret key (can also be set via OMX_SECRET_KEY env var)
            base_url: Base URL for the OMX API (can also be set via OMX_API_BASE_URL env var)

        Raises:
            ValueError: If client_id or secret_key are not provided
        """
        self.client_id = client_id or os.getenv('OMX_CLIENT_ID')
        self.secret_key = secret_key or os.getenv('OMX_SECRET_KEY')
        self.base_url = base_url or os.getenv('OMX_API_BASE_URL', 'https://blhilidnsybhfdmwqsrx.supabase.co/functions/v1')

        if not self.client_id or not self.secret_key:
            raise ValueError(
                "client_id and secret_key are required. "
                "Set via parameters or OMX_CLIENT_ID/OMX_SECRET_KEY environment variables."
            )

        self._client = httpx.AsyncClient()
        self._token: Optional[str] = None

        # Initialize all module managers
        self.notification = NotificationManager(self)
        self.email = EmailManager(self)
        self.geo_trigger = GeoTriggerManager(self)
        self.beacon = BeaconManager(self)
        self.webhook = WebhookManager(self)
        self.campaign = CampaignManager(self)
        self.workflow = WorkflowManager(self)
        self.analytics = AnalyticsManager(self)
        self.segment = SegmentManager(self)
        self.events = EventsManager(self)

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None
    ) -> Any:
        """Make an HTTP request to the OMX API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Optional request body data
            params: Optional query parameters

        Returns:
            Response data (JSON parsed) or empty dict

        Raises:
            Exception: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.secret_key}',
            'X-Client-ID': self.client_id,
        }

        try:
            if method.upper() == 'GET':
                response = await self._client.get(url, headers=headers, params=params)
            elif method.upper() == 'POST':
                response = await self._client.post(url, headers=headers, json=data)
            elif method.upper() == 'PUT':
                response = await self._client.put(url, headers=headers, json=data)
            elif method.upper() == 'DELETE':
                response = await self._client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()

            if response.content:
                return response.json()
            return {}

        except httpx.HTTPStatusError as e:
            raise Exception(f"API Error: {e.response.status_code} {e.response.text}")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")

    async def close(self) -> None:
        """Close the HTTP client.

        Call this when you're done using the client if not using context manager.
        """
        await self._client.aclose()

    async def __aenter__(self):
        """Async context manager entry.

        Returns:
            self for use in 'async with' statement
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit.

        Automatically closes the HTTP client.
        """
        await self.close()


# Export main classes and functions
__all__ = [
    'OMXClient',
    'Location',
    'GeoFence',
    'NotificationResult',
    'NotificationHistory',
    'NotificationStatus',
    'EmailResult',
    'EmailCampaign',
    'EmailTemplate',
    'Beacon',
    'Webhook',
    'WebhookDelivery',
    'Campaign',
    'GeoEvent',
    'Workflow',
    'Segment',
    'Event',
    'AnalyticsData',
]
