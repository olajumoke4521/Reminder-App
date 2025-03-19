
importScripts('https://www.gstatic.com/firebasejs/9.6.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.6.1/firebase-messaging-compat.js');

firebase.initializeApp({
  apiKey: "{{ config.apiKey }}",
  authDomain: "{{ config.authDomain }}",
  projectId: "{{ config.projectId }}",
  storageBucket: "{{ config.storageBucket }}",
  messagingSenderId: "{{ config.messagingSenderId }}",
  appId: "{{ config.appId }}"
});

const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage((payload) => {
  console.log('Received background message', payload);
  
  const notificationTitle = payload.notification.title || 'New Reminder';
  const notificationOptions = {
    body: payload.notification.body || 'You have a new reminder',
    icon: '/static/reminders/images/notification-icon.png',
    data: payload.data || {}
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification click
self.addEventListener('notificationclick', function(event) {
  console.log('[firebase-messaging-sw.js] Notification clicked', event);
  const notification = event.notification;
  const data = notification.data || {};
  
  
  // Close the notification
  notification.close();
  
  // Handle click action - open the app on the reminder detail page
  if (data && data.reminder_id) {
    const urlToOpen = new URL(`/reminders/${data.reminder_id}/`, self.location.origin);

    if (data.subtask_id) {
      urlToOpen.pathname = `/reminders/${data.reminder_id}/subtasks/${data.subtask_id}/`;
    }
    
    event.waitUntil(
      clients.matchAll({type: 'window'}).then(windowClients => {
        // Check if there is already a window/tab open with the target URL
        for (var i = 0; i < windowClients.length; i++) {
          var client = windowClients[i];
          // If so, focus it
          if (client.url === urlToOpen.href && 'focus' in client) {
            return client.focus();
          }
        }
        // If not, open a new window/tab
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen.href);
        }
      })
    );
  }
});

// Log service worker activation
self.addEventListener('activate', event => {
  console.log('[firebase-messaging-sw.js] Service worker activated');
});

// Log service worker installation
self.addEventListener('install', event => {
  console.log('[firebase-messaging-sw.js] Service worker installed');
  self.skipWaiting();
});