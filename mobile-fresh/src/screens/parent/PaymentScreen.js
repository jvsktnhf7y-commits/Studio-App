import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, Alert, TouchableOpacity, ScrollView, KeyboardAvoidingView, Platform, TextInput, Linking, Clipboard } from 'react-native';
import { useStripe, StripeProvider } from '@stripe/stripe-react-native';

const STRIPE_PK = 'pk_test_51TiPs2C4vwE62RZDV0PMKClgT35K7BwAEJI9Oof3m7FVf8DuwgCG2BxbWQdXDBlDnWRhcaO1bYG4hdGDLJd7QVxQ0032CpqnPE';
import { LinearGradient } from 'expo-linear-gradient';
import Button from '../../components/Button';
import { parentCreatePaymentIntent, parentGetDashboard, parentGetPaymentDue, parentGetPaymentHandles } from '../../services/api';
import { COLORS, GRADIENT } from '../../theme';

const PAYMENT_METHODS = [
  { id: 'card',  label: '💳  Pay by Card',  subtitle: '$4.00 convenience fee' },
  { id: 'cash',  label: '💵  Cash',         subtitle: 'Pay your teacher directly' },
  { id: 'venmo', label: '💜  Venmo',        subtitle: 'Send to your teacher directly' },
  { id: 'zelle', label: '💛  Zelle',        subtitle: 'Send to your teacher directly' },
];

function ParentPaymentInner({ navigation }) {
  const { initPaymentSheet, presentPaymentSheet } = useStripe();
  const [balance,      setBalance]      = useState(0);
  const [amount,       setAmount]       = useState('');
  const [method,       setMethod]       = useState('card');
  const [loading,      setLoading]      = useState(false);
  const [paid,         setPaid]         = useState(null);
  const [weekLessons,  setWeekLessons]  = useState(null);
  const [amountDue,    setAmountDue]    = useState(null);
  const [rate,         setRate]         = useState(null);
  const [handles,      setHandles]      = useState({});

  useEffect(() => {
    parentGetDashboard().then(d => { if (d.ok) setBalance(d.balance); }).catch(() => {});
    parentGetPaymentDue().then(d => {
      if (d.ok) {
        setWeekLessons(d.week_lessons);
        setAmountDue(d.amount_due);
        setRate(d.rate);
        if (d.amount_due > 0 && !amount) setAmount(d.amount_due.toFixed(2));
      }
    }).catch(() => {});
    parentGetPaymentHandles().then(d => { if (d.ok) setHandles(d); }).catch(() => {});
  }, []);

  async function handleCardPayment() {
    const amt = parseFloat(amount);
    if (!amt || amt <= 0) { Alert.alert('Invalid amount', 'Please enter an amount.'); return; }
    setLoading(true);
    try {
      const res = await parentCreatePaymentIntent(Math.round(amt * 100), 'Lesson payment');
      if (!res.ok) { Alert.alert('Error', res.error || 'Could not create payment.'); return; }

      const { error: initError } = await initPaymentSheet({
        merchantDisplayName: 'Maestro Music Studio',
        paymentIntentClientSecret: res.client_secret,
      });
      if (initError) { Alert.alert('Error', initError.message); return; }

      const { error: presentError } = await presentPaymentSheet();
      if (presentError) {
        if (presentError.code !== 'Canceled') Alert.alert('Payment failed', presentError.message);
        return;
      }
      setPaid({ amount: amt, fee: res.fee_cents / 100, method: 'card' });
    } catch { Alert.alert('Error', 'Something went wrong. Please try again.'); }
    finally { setLoading(false); }
  }

  function handleOfflineMethod() {
    const m = PAYMENT_METHODS.find(p => p.id === method);
    setPaid({ amount: parseFloat(amount) || 0, fee: 0, method: m?.id || method });
  }

  if (paid) {
    const isCard = paid.method === 'card';
    return (
      <View style={styles.successContainer}>
        <LinearGradient colors={['#667eea', '#f093fb']} style={styles.successBanner} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
          <Text style={styles.successEmoji}>{isCard ? '💳' : '✅'}</Text>
          <Text style={styles.successTitle}>{isCard ? 'Payment Sent!' : 'Got it!'}</Text>
          <Text style={styles.successSub}>{isCard ? "Your payment is on its way to your teacher." : "We'll let your teacher know."}</Text>
        </LinearGradient>
        <View style={styles.successBody}>
          <View style={styles.resultRow}><Text style={styles.resultLabel}>Amount</Text><Text style={[styles.resultValue, { color: COLORS.success }]}>${paid.amount.toFixed(2)}</Text></View>
          {paid.fee > 0 && <View style={styles.resultRow}><Text style={styles.resultLabel}>Convenience fee</Text><Text style={styles.resultValue}>${paid.fee.toFixed(2)}</Text></View>}
          <View style={[styles.resultRow, { borderBottomWidth: 0 }]}><Text style={styles.resultLabel}>Method</Text><Text style={styles.resultValue}>{paid.method.charAt(0).toUpperCase() + paid.method.slice(1)}</Text></View>
          <Button label="← Back" onPress={() => setPaid(null)} style={{ marginTop: 24 }} />
        </View>
      </View>
    );
  }

  const balanceColor = balance < 0 ? COLORS.danger : balance < 50 ? COLORS.warning : COLORS.success;

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView style={styles.container} contentContainerStyle={{ padding: 16, paddingBottom: 48 }} keyboardShouldPersistTaps="handled">
        <View style={[styles.balanceCard, { borderColor: balanceColor }]}>
          <Text style={styles.balanceLabel}>Current balance</Text>
          <Text style={[styles.balanceValue, { color: balanceColor }]}>${balance.toFixed(2)}</Text>
        </View>

        {weekLessons !== null && weekLessons > 0 && (
          <View style={styles.dueCard}>
            <Text style={styles.dueTitle}>💡 Payment requested</Text>
            <View style={styles.dueRow}>
              <Text style={styles.dueLine}>{weekLessons} lesson{weekLessons !== 1 ? 's' : ''} this week</Text>
              <Text style={styles.dueRate}>× ${rate?.toFixed(2)}/lesson</Text>
            </View>
            <View style={[styles.dueRow, { borderTopWidth: 1, borderTopColor: '#e4e4e7', marginTop: 8, paddingTop: 10 }]}>
              <Text style={[styles.dueLine, { fontWeight: '800', color: '#18181b' }]}>Total due</Text>
              <Text style={[styles.dueRate, { fontWeight: '800', color: COLORS.primary, fontSize: 18 }]}>${amountDue?.toFixed(2)}</Text>
            </View>
          </View>
        )}

        {(handles.venmo || handles.cashapp || handles.paypal || handles.zelle) && (
          <View style={{ marginBottom: 16 }}>
            <Text style={styles.label}>Pay your teacher directly</Text>
            {handles.venmo ? (
              <TouchableOpacity style={styles.handleBtn} onPress={() => {
                const amt = parseFloat(amount) || 0;
                const note = encodeURIComponent('Lesson payment');
                Linking.openURL(`venmo://paycharge?txn=pay&recipients=${handles.venmo.replace('@','')}&amount=${amt}&note=${note}`);
              }}>
                <Text style={styles.handleIcon}>💜</Text>
                <View style={{ flex: 1 }}>
                  <Text style={styles.handleLabel}>Pay via Venmo</Text>
                  <Text style={styles.handleSub}>{handles.venmo}</Text>
                </View>
                <Text style={styles.handleArrow}>↗</Text>
              </TouchableOpacity>
            ) : null}
            {handles.cashapp ? (
              <TouchableOpacity style={styles.handleBtn} onPress={() => {
                const amt = parseFloat(amount) || 0;
                const tag = handles.cashapp.startsWith('$') ? handles.cashapp.slice(1) : handles.cashapp;
                Linking.openURL(`https://cash.app/$${tag}/${amt}`);
              }}>
                <Text style={styles.handleIcon}>💚</Text>
                <View style={{ flex: 1 }}>
                  <Text style={styles.handleLabel}>Pay via Cash App</Text>
                  <Text style={styles.handleSub}>{handles.cashapp}</Text>
                </View>
                <Text style={styles.handleArrow}>↗</Text>
              </TouchableOpacity>
            ) : null}
            {handles.paypal ? (
              <TouchableOpacity style={styles.handleBtn} onPress={() => {
                const amt = parseFloat(amount) || 0;
                Linking.openURL(`https://paypal.me/${handles.paypal}/${amt}`);
              }}>
                <Text style={styles.handleIcon}>🔵</Text>
                <View style={{ flex: 1 }}>
                  <Text style={styles.handleLabel}>Pay via PayPal</Text>
                  <Text style={styles.handleSub}>paypal.me/{handles.paypal}</Text>
                </View>
                <Text style={styles.handleArrow}>↗</Text>
              </TouchableOpacity>
            ) : null}
            {handles.zelle ? (
              <TouchableOpacity style={styles.handleBtn} onPress={() => {
                Clipboard.setString(handles.zelle);
                Alert.alert('Copied!', `${handles.zelle} copied. Open your bank app and send via Zelle.`);
              }}>
                <Text style={styles.handleIcon}>💛</Text>
                <View style={{ flex: 1 }}>
                  <Text style={styles.handleLabel}>Pay via Zelle</Text>
                  <Text style={styles.handleSub}>{handles.zelle} — tap to copy</Text>
                </View>
                <Text style={styles.handleArrow}>⧉</Text>
              </TouchableOpacity>
            ) : null}
          </View>
        )}

        <Text style={[styles.label, { marginTop: 4 }]}>Or pay by card</Text>
        <Text style={styles.label}>Payment amount ($)</Text>
        <TextInput style={styles.input} value={amount} onChangeText={setAmount} placeholder="0.00" placeholderTextColor={COLORS.muted} keyboardType="decimal-pad" />

        <Text style={styles.label}>How would you like to pay?</Text>
        {PAYMENT_METHODS.map(m => (
          <TouchableOpacity key={m.id} style={[styles.methodCard, method === m.id && styles.methodCardActive]} onPress={() => setMethod(m.id)} activeOpacity={0.75}>
            <View style={{ flex: 1 }}>
              <Text style={[styles.methodLabel, method === m.id && { color: COLORS.primary }]}>{m.label}</Text>
              <Text style={styles.methodSub}>{m.subtitle}</Text>
            </View>
            {method === m.id && <Text style={styles.checkmark}>✓</Text>}
          </TouchableOpacity>
        ))}

        {method === 'card' && (
          <View style={styles.feeNotice}>
            <Text style={styles.feeText}>A $4.00 convenience fee covers card processing. No fee for cash, Venmo, or Zelle.</Text>
          </View>
        )}

        <Button
          label={method === 'card' ? `Pay $${((parseFloat(amount) || 0) + 4).toFixed(2)} by Card →` : `Record ${method.charAt(0).toUpperCase() + method.slice(1)} Payment →`}
          onPress={method === 'card' ? handleCardPayment : handleOfflineMethod}
          loading={loading}
          style={{ marginTop: 20 }}
        />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

export default function ParentPaymentScreen(props) {
  return (
    <StripeProvider publishableKey={STRIPE_PK}>
      <ParentPaymentInner {...props} />
    </StripeProvider>
  );
}

const styles = StyleSheet.create({
  container:        { flex: 1, backgroundColor: COLORS.bg },
  balanceCard:      { backgroundColor: '#fff', borderRadius: 16, padding: 16, marginBottom: 20, borderWidth: 1.5, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  balanceLabel:     { fontSize: 13, color: COLORS.subtext, fontWeight: '600' },
  balanceValue:     { fontSize: 24, fontWeight: '800' },
  label:            { fontSize: 13, fontWeight: '600', color: COLORS.subtext, marginBottom: 8, marginTop: 16 },
  input:            { backgroundColor: '#fff', borderWidth: 1.5, borderColor: COLORS.border, borderRadius: 12, paddingHorizontal: 14, height: 50, fontSize: 18, color: COLORS.text, fontWeight: '700' },
  methodCard:       { backgroundColor: '#fff', borderWidth: 1.5, borderColor: COLORS.border, borderRadius: 14, padding: 16, marginBottom: 10, flexDirection: 'row', alignItems: 'center' },
  methodCardActive: { borderColor: COLORS.primary, backgroundColor: '#f5f3ff' },
  methodLabel:      { fontSize: 15, fontWeight: '700', color: COLORS.text, marginBottom: 2 },
  methodSub:        { fontSize: 12, color: COLORS.muted },
  checkmark:        { color: COLORS.primary, fontWeight: '800', fontSize: 18 },
  feeNotice:        { backgroundColor: '#fffaf0', borderRadius: 10, padding: 12, marginTop: 4, borderWidth: 1, borderColor: COLORS.warning },
  feeText:          { fontSize: 13, color: COLORS.text, lineHeight: 18 },
  handleBtn:        { backgroundColor: '#fff', borderRadius: 14, borderWidth: 1.5, borderColor: COLORS.border, padding: 14, marginBottom: 10, flexDirection: 'row', alignItems: 'center', gap: 12 },
  handleIcon:       { fontSize: 22, width: 28, textAlign: 'center' },
  handleLabel:      { fontSize: 15, fontWeight: '700', color: COLORS.text, marginBottom: 1 },
  handleSub:        { fontSize: 12, color: COLORS.muted },
  handleArrow:      { fontSize: 18, color: COLORS.muted, fontWeight: '700' },
  dueCard:          { backgroundColor: '#f0f4ff', borderRadius: 16, padding: 16, marginBottom: 16, borderWidth: 1.5, borderColor: COLORS.primary },
  dueTitle:         { fontSize: 13, fontWeight: '700', color: COLORS.primary, marginBottom: 12 },
  dueRow:           { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  dueLine:          { fontSize: 15, fontWeight: '600', color: '#3f3f46' },
  dueRate:          { fontSize: 15, fontWeight: '600', color: '#52525b' },
  successContainer: { flex: 1, backgroundColor: COLORS.bg },
  successBanner:    { paddingTop: 60, paddingBottom: 40, alignItems: 'center', paddingHorizontal: 24 },
  successEmoji:     { fontSize: 56, marginBottom: 8 },
  successTitle:     { fontSize: 32, fontWeight: '800', color: '#fff', marginBottom: 6 },
  successSub:       { fontSize: 15, color: 'rgba(255,255,255,0.8)', textAlign: 'center' },
  successBody:      { padding: 24 },
  resultRow:        { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: COLORS.border },
  resultLabel:      { fontSize: 15, color: COLORS.subtext },
  resultValue:      { fontSize: 15, fontWeight: '700', color: COLORS.text },
});
