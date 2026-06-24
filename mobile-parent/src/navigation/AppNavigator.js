import React, { useEffect, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { ActivityIndicator, Text, TouchableOpacity, View } from 'react-native';
import { StripeProvider } from '@stripe/stripe-react-native';

import LoginScreen     from '../screens/LoginScreen';
import DashboardScreen from '../screens/DashboardScreen';
import NotesScreen     from '../screens/NotesScreen';
import PaymentScreen   from '../screens/PaymentScreen';
import { isLoggedIn, logout } from '../services/api';
import { COLORS } from '../theme';

const Stack = createNativeStackNavigator();
const Tab   = createBottomTabNavigator();

const STRIPE_PK = 'pk_live_YOUR_PUBLISHABLE_KEY'; // replace after Stripe Connect is set up

function TabIcon({ label, focused }) {
  const icons = { Home: '🏠', Notes: '📝', Pay: '💳' };
  return <Text style={{ fontSize: focused ? 22 : 19, opacity: focused ? 1 : 0.5 }}>{icons[label]}</Text>;
}

function MainTabs({ navigation }) {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused }) => <TabIcon label={route.name} focused={focused} />,
        tabBarActiveTintColor:   COLORS.primary,
        tabBarInactiveTintColor: COLORS.muted,
        tabBarLabelStyle:  { fontSize: 12, fontWeight: '600', marginBottom: 4 },
        tabBarStyle: { backgroundColor: '#fff', borderTopColor: COLORS.border, borderTopWidth: 1, height: 62, paddingTop: 6 },
        headerStyle:      { backgroundColor: '#fff', borderBottomWidth: 0, elevation: 0, shadowOpacity: 0 },
        headerTitleStyle: { color: COLORS.text, fontWeight: '800', fontSize: 19 },
        headerTintColor:  COLORS.text,
      })}
    >
      <Tab.Screen name="Home" component={DashboardScreen} options={{
        title: 'Dashboard',
        headerRight: () => (
          <TouchableOpacity onPress={async () => { await logout(); navigation.replace('Login'); }} style={{ marginRight: 16 }}>
            <Text style={{ color: COLORS.primary, fontWeight: '600', fontSize: 15 }}>Logout</Text>
          </TouchableOpacity>
        ),
      }} />
      <Tab.Screen name="Notes" component={NotesScreen}   options={{ title: 'Lesson Notes' }} />
      <Tab.Screen name="Pay"   component={PaymentScreen} options={{ title: 'Make a Payment' }} />
    </Tab.Navigator>
  );
}

export default function AppNavigator() {
  const [checking, setChecking] = useState(true);
  const [authed,   setAuthed]   = useState(false);

  useEffect(() => {
    isLoggedIn().then(v => { setAuthed(v); setChecking(false); });
  }, []);

  if (checking) return (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: COLORS.bg }}>
      <ActivityIndicator size="large" color={COLORS.primary} />
    </View>
  );

  return (
    <StripeProvider publishableKey={STRIPE_PK}>
      <NavigationContainer>
        <Stack.Navigator initialRouteName={authed ? 'Main' : 'Login'} screenOptions={{ headerShown: false }}>
          <Stack.Screen name="Login" component={LoginScreen} />
          <Stack.Screen name="Main"  component={MainTabs} />
        </Stack.Navigator>
      </NavigationContainer>
    </StripeProvider>
  );
}
