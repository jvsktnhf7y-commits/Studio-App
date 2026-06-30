import React, { useState, useEffect } from 'react';
import {
  View, Text, TextInput, Switch, StyleSheet,
  ScrollView, Alert, ActivityIndicator, TouchableOpacity,
} from 'react-native';
import { getSettings, saveSettings } from '../services/api';
import { COLORS, SHADOW_CARD } from '../theme';

export default function SettingsScreen({ navigation }) {
  const [loading,   setLoading]   = useState(true);
  const [saving,    setSaving]    = useState(false);
  const [keywords,  setKeywords]  = useState('');
  const [showAll,   setShowAll]   = useState(true);
  const [venmo,     setVenmo]     = useState('');
  const [cashapp,   setCashapp]   = useState('');
  const [paypal,    setPaypal]    = useState('');
  const [zelle,     setZelle]     = useState('');

  useEffect(() => {
    getSettings()
      .then(d => {
        if (d.ok) {
          setKeywords((d.lesson_keywords || []).join(', '));
          setShowAll(d.show_all !== false);
          setVenmo(d.venmo || '');
          setCashapp(d.cashapp || '');
          setPaypal(d.paypal || '');
          setZelle(d.zelle || '');
        }
      })
      .catch(() => Alert.alert('Error', 'Could not load settings.'))
      .finally(() => setLoading(false));
  }, []);

  async function handleSave() {
    setSaving(true);
    try {
      const kwList = keywords.split(',').map(k => k.trim()).filter(Boolean);
      await saveSettings({ lesson_keywords: kwList, show_all: showAll, venmo, cashapp, paypal, zelle });
      Alert.alert('Saved', 'Settings updated.');
    } catch {
      Alert.alert('Error', 'Could not save settings.');
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <View style={styles.center}><ActivityIndicator size="large" color={COLORS.primary} /></View>;
  }

  return (
    <ScrollView style={styles.root} contentContainerStyle={styles.body}>
      <Text style={styles.sectionLabel}>Calendar Settings</Text>
      <View style={styles.card}>
        <Text style={styles.label}>Lesson Keywords</Text>
        <Text style={styles.hint}>Events matching these words appear on the dashboard as lessons.</Text>
        <TextInput
          style={styles.input}
          value={keywords}
          onChangeText={setKeywords}
          placeholder="e.g. lesson, piano, guitar"
          placeholderTextColor={COLORS.muted}
          multiline
        />
      </View>

      <View style={styles.card}>
        <View style={styles.switchRow}>
          <View style={{ flex: 1 }}>
            <Text style={styles.label}>Show unregistered events</Text>
            <Text style={styles.hint}>Show lesson-like events for students not in your roster.</Text>
          </View>
          <Switch
            value={showAll}
            onValueChange={setShowAll}
            trackColor={{ true: COLORS.primary }}
            thumbColor="#fff"
          />
        </View>
      </View>

      <Text style={[styles.sectionLabel, { marginTop: 8 }]}>Payment Handles</Text>
      <Text style={{ fontSize: 12, color: COLORS.muted, marginBottom: 10, lineHeight: 17 }}>
        Parents will see buttons to pay you directly via these services.
      </Text>
      <View style={styles.card}>
        {[
          { label: 'Venmo username', placeholder: '@yourname', value: venmo, setter: setVenmo },
          { label: 'Cash App $tag', placeholder: '$yourtag', value: cashapp, setter: setCashapp },
          { label: 'PayPal.me slug', placeholder: 'yourname (from paypal.me/yourname)', value: paypal, setter: setPaypal },
          { label: 'Zelle (phone or email)', placeholder: '+1 555-555-5555', value: zelle, setter: setZelle },
        ].map(({ label, placeholder, value, setter }) => (
          <View key={label} style={{ marginBottom: 14 }}>
            <Text style={styles.label}>{label}</Text>
            <TextInput
              style={styles.input}
              value={value}
              onChangeText={setter}
              placeholder={placeholder}
              placeholderTextColor={COLORS.muted}
              autoCapitalize="none"
              autoCorrect={false}
            />
          </View>
        ))}
      </View>

      <TouchableOpacity
        style={[styles.saveBtn, saving && { opacity: 0.6 }]}
        onPress={handleSave}
        disabled={saving}
      >
        <Text style={styles.saveBtnText}>{saving ? 'Saving…' : 'Save Settings'}</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  root:         { flex: 1, backgroundColor: COLORS.bg },
  body:         { padding: 20, paddingBottom: 40 },
  center:       { flex: 1, justifyContent: 'center', alignItems: 'center' },
  sectionLabel: { fontSize: 11, fontWeight: '700', color: COLORS.muted, textTransform: 'uppercase', letterSpacing: 1.2, marginBottom: 10 },
  card:         { backgroundColor: '#fff', borderRadius: 14, padding: 16, marginBottom: 12, borderWidth: 1, borderColor: COLORS.border, ...SHADOW_CARD },
  label:        { fontSize: 14, fontWeight: '700', color: COLORS.text, marginBottom: 4 },
  hint:         { fontSize: 12, color: COLORS.muted, marginBottom: 10, lineHeight: 17 },
  input:        { borderWidth: 1.5, borderColor: COLORS.border, borderRadius: 10, padding: 12, fontSize: 14, color: COLORS.text, minHeight: 52 },
  switchRow:    { flexDirection: 'row', alignItems: 'center', gap: 12 },
  saveBtn:      { backgroundColor: COLORS.primary, borderRadius: 14, height: 52, alignItems: 'center', justifyContent: 'center', marginTop: 8 },
  saveBtnText:  { color: '#fff', fontWeight: '700', fontSize: 16 },
});
