import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, Alert, Linking, ActivityIndicator } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Button from '../components/Button';
import { COLORS, GRADIENT } from '../theme';
import AsyncStorage from '@react-native-async-storage/async-storage';

const BASE_URL = 'https://studio-app-7y7z.onrender.com';

export default function StripeConnectScreen() {
  const [status,  setStatus]  = useState(null); // null | 'loading' | 'connected' | 'not_connected'
  const [loading, setLoading] = useState(false);

  async function checkStatus() {
    setStatus('loading');
    try {
      const session = await AsyncStorage.getItem('studio_session');
      const res = await fetch(`${BASE_URL}/api/mobile/teacher/stripe-status`, {
        headers: { 'Authorization': `Bearer ${session}` },
      });
      const data = await res.json();
      setStatus(data.ready ? 'connected' : 'not_connected');
    } catch { setStatus('not_connected'); }
  }

  useEffect(() => { checkStatus(); }, []);

  async function handleConnect() {
    setLoading(true);
    try {
      const session = await AsyncStorage.getItem('studio_session');
      const emailKey = 'teacher_email';
      const email = await AsyncStorage.getItem(emailKey) || '';
      const res = await fetch(`${BASE_URL}/api/mobile/teacher/stripe-connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${session}` },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (data.ok && data.url) {
        await Linking.openURL(data.url);
      } else {
        Alert.alert('Error', data.error || 'Could not start Stripe setup.');
      }
    } catch { Alert.alert('Error', 'Could not connect to server.'); }
    finally { setLoading(false); }
  }

  if (status === 'loading' || status === null) {
    return <View style={styles.center}><ActivityIndicator size="large" color={COLORS.primary} /></View>;
  }

  if (status === 'connected') {
    return (
      <View style={styles.container}>
        <LinearGradient colors={['#48bb78', '#38a169']} style={styles.banner} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
          <Text style={styles.bannerEmoji}>✅</Text>
          <Text style={styles.bannerTitle}>Payments Active</Text>
          <Text style={styles.bannerSub}>Parents can pay you directly through their app.</Text>
        </LinearGradient>
        <View style={styles.body}>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Convenience fee charged to parent</Text>
            <Text style={styles.infoValue}>$3.00</Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>You receive</Text>
            <Text style={[styles.infoValue, { color: COLORS.success }]}>Full lesson amount</Text>
          </View>
          <View style={[styles.infoRow, { borderBottomWidth: 0 }]}>
            <Text style={styles.infoLabel}>Processing</Text>
            <Text style={styles.infoValue}>Stripe</Text>
          </View>
          <Button label="Refresh Status" onPress={checkStatus} variant="secondary" style={{ marginTop: 24 }} />
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <LinearGradient colors={GRADIENT} style={styles.banner} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
        <Text style={styles.bannerEmoji}>💳</Text>
        <Text style={styles.bannerTitle}>Accept Payments</Text>
        <Text style={styles.bannerSub}>Let parents pay you directly through the Parent App.</Text>
      </LinearGradient>
      <View style={styles.body}>
        <Text style={styles.howTitle}>How it works</Text>
        <View style={styles.step}><Text style={styles.stepNum}>1</Text><Text style={styles.stepText}>Connect your Stripe account (takes 5 minutes)</Text></View>
        <View style={styles.step}><Text style={styles.stepNum}>2</Text><Text style={styles.stepText}>Parents see a "Pay" tab in their app</Text></View>
        <View style={styles.step}><Text style={styles.stepNum}>3</Text><Text style={styles.stepText}>They pay by card — money goes straight to your bank</Text></View>
        <View style={styles.step}><Text style={styles.stepNum}>4</Text><Text style={styles.stepText}>$3.00 convenience fee added for the parent — you keep the full lesson amount</Text></View>
        <Button label="Set Up Payments →" onPress={handleConnect} loading={loading} style={{ marginTop: 28 }} />
        <Text style={styles.note}>You'll be taken to Stripe to securely connect your bank account. Return to the app when done.</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container:   { flex: 1, backgroundColor: COLORS.bg },
  center:      { flex: 1, justifyContent: 'center', alignItems: 'center' },
  banner:      { paddingTop: 48, paddingBottom: 36, alignItems: 'center', paddingHorizontal: 24 },
  bannerEmoji: { fontSize: 52, marginBottom: 10 },
  bannerTitle: { fontSize: 28, fontWeight: '800', color: '#fff', marginBottom: 6 },
  bannerSub:   { fontSize: 15, color: 'rgba(255,255,255,0.8)', textAlign: 'center' },
  body:        { padding: 24 },
  howTitle:    { fontSize: 16, fontWeight: '800', color: COLORS.text, marginBottom: 16 },
  step:        { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 14 },
  stepNum:     { width: 28, height: 28, borderRadius: 14, backgroundColor: '#ede9fe', color: COLORS.primary, fontWeight: '800', fontSize: 14, textAlign: 'center', lineHeight: 28, marginRight: 12 },
  stepText:    { flex: 1, fontSize: 14, color: COLORS.text, lineHeight: 20, paddingTop: 4 },
  note:        { fontSize: 12, color: COLORS.muted, textAlign: 'center', marginTop: 16, lineHeight: 18 },
  infoRow:     { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: COLORS.border },
  infoLabel:   { fontSize: 14, color: COLORS.subtext },
  infoValue:   { fontSize: 14, fontWeight: '700', color: COLORS.text },
});
