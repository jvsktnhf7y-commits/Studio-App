import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  Alert, ActivityIndicator, RefreshControl, TextInput, Modal, ScrollView,
} from 'react-native';
import { getMakeupCredits, getMakeupSlots, addMakeupSlot, deleteMakeupSlot, adjustMakeupCredit } from '../services/api';
import { COLORS } from '../theme';

export default function MakeupSlotsScreen() {
  const [credits,    setCredits]    = useState({});
  const [slots,      setSlots]      = useState([]);
  const [loading,    setLoading]    = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showAdd,    setShowAdd]    = useState(false);
  const [saving,     setSaving]     = useState(false);

  const [date,     setDate]     = useState('');
  const [time,     setTime]     = useState('');
  const [duration, setDuration] = useState('60');
  const [note,     setNote]     = useState('');

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true); else setLoading(true);
    try {
      const [c, s] = await Promise.all([getMakeupCredits(), getMakeupSlots()]);
      if (c.ok) setCredits(c.credits);
      if (s.ok) setSlots(s.slots);
    } catch { Alert.alert('Error', 'Could not load make-up data.'); }
    finally { setLoading(false); setRefreshing(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleAdd() {
    if (!date || !time) { Alert.alert('Required', 'Please enter a date and time.'); return; }
    setSaving(true);
    try {
      const res = await addMakeupSlot(date, time, parseInt(duration) || 60, note);
      if (res.ok) {
        setShowAdd(false); setDate(''); setTime(''); setDuration('60'); setNote('');
        load();
        Alert.alert('Slot added', 'Parents with make-up credits have been notified.');
      } else { Alert.alert('Error', res.error || 'Could not add slot.'); }
    } catch { Alert.alert('Error', 'Something went wrong.'); }
    finally { setSaving(false); }
  }

  async function handleDelete(slot) {
    Alert.alert('Remove slot', `Remove ${slot.date} at ${slot.time}?`, [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Remove', style: 'destructive', onPress: async () => {
        try {
          await deleteMakeupSlot(slot.id);
          setSlots(prev => prev.filter(s => s.id !== slot.id));
        } catch { Alert.alert('Error', 'Could not remove slot.'); }
      }},
    ]);
  }

  async function handleAdjust(studentName, delta) {
    try {
      const res = await adjustMakeupCredit(studentName, delta);
      if (res.ok) setCredits(prev => ({ ...prev, [studentName]: res.credits }));
    } catch { Alert.alert('Error', 'Could not adjust credit.'); }
  }

  if (loading) return <View style={styles.center}><ActivityIndicator size="large" color={COLORS.primary} /></View>;

  const creditEntries = Object.entries(credits).filter(([, v]) => v > 0);

  return (
    <View style={styles.container}>
      <ScrollView
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={COLORS.primary} />}
        contentContainerStyle={{ padding: 16, paddingBottom: 40 }}
      >
        {/* Credits section */}
        <Text style={styles.sectionLabel}>Student Credits</Text>
        {creditEntries.length === 0 ? (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyText}>No make-up credits yet. Credits are issued automatically when a lesson is missed or cancelled.</Text>
          </View>
        ) : (
          creditEntries.map(([name, count]) => (
            <View key={name} style={styles.creditCard}>
              <View style={{ flex: 1 }}>
                <Text style={styles.creditName}>{name}</Text>
                <Text style={styles.creditCount}>{count} credit{count !== 1 ? 's' : ''}</Text>
              </View>
              <View style={styles.adjRow}>
                <TouchableOpacity style={styles.adjBtn} onPress={() => handleAdjust(name, -1)}>
                  <Text style={styles.adjBtnText}>−</Text>
                </TouchableOpacity>
                <TouchableOpacity style={[styles.adjBtn, { backgroundColor: COLORS.success }]} onPress={() => handleAdjust(name, 1)}>
                  <Text style={styles.adjBtnText}>+</Text>
                </TouchableOpacity>
              </View>
            </View>
          ))
        )}

        {/* Available slots section */}
        <View style={styles.slotHeader}>
          <Text style={styles.sectionLabel}>Available Slots</Text>
          <TouchableOpacity style={styles.addBtn} onPress={() => setShowAdd(true)}>
            <Text style={styles.addBtnText}>+ Add Slot</Text>
          </TouchableOpacity>
        </View>

        {slots.length === 0 ? (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyText}>No open slots. Tap "+ Add Slot" to post a time — parents with credits will be notified immediately.</Text>
          </View>
        ) : (
          slots.map(slot => (
            <View key={slot.id} style={styles.slotCard}>
              <View style={{ flex: 1 }}>
                <Text style={styles.slotDate}>{slot.date}</Text>
                <Text style={styles.slotTime}>{slot.time} · {slot.duration} min</Text>
                {!!slot.note && <Text style={styles.slotNote}>{slot.note}</Text>}
                {slot.booked_by && <Text style={styles.bookedBadge}>✅ Booked by {slot.booked_by}</Text>}
              </View>
              {!slot.booked_by && (
                <TouchableOpacity onPress={() => handleDelete(slot)}>
                  <Text style={styles.deleteBtn}>✕</Text>
                </TouchableOpacity>
              )}
            </View>
          ))
        )}
      </ScrollView>

      {/* Add slot modal */}
      <Modal visible={showAdd} transparent animationType="slide" onRequestClose={() => setShowAdd(false)}>
        <TouchableOpacity style={styles.modalBackdrop} activeOpacity={1} onPress={() => setShowAdd(false)} />
        <View style={styles.modalSheet}>
          <Text style={styles.modalTitle}>Add Make-up Slot</Text>
          <Text style={styles.modalLabel}>Date (YYYY-MM-DD)</Text>
          <TextInput style={styles.input} value={date} onChangeText={setDate} placeholder="2025-07-15" placeholderTextColor={COLORS.muted} autoCorrect={false} />
          <Text style={styles.modalLabel}>Time</Text>
          <TextInput style={styles.input} value={time} onChangeText={setTime} placeholder="3:00 PM" placeholderTextColor={COLORS.muted} autoCorrect={false} />
          <Text style={styles.modalLabel}>Duration (minutes)</Text>
          <TextInput style={styles.input} value={duration} onChangeText={setDuration} keyboardType="number-pad" placeholder="60" placeholderTextColor={COLORS.muted} />
          <Text style={styles.modalLabel}>Note (optional)</Text>
          <TextInput style={styles.input} value={note} onChangeText={setNote} placeholder="e.g. Studio B available" placeholderTextColor={COLORS.muted} />
          <TouchableOpacity style={[styles.saveBtn, saving && { opacity: 0.6 }]} onPress={handleAdd} disabled={saving}>
            <Text style={styles.saveBtnText}>{saving ? 'Saving…' : 'Add Slot & Notify Parents'}</Text>
          </TouchableOpacity>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container:     { flex: 1, backgroundColor: COLORS.bg },
  center:        { flex: 1, justifyContent: 'center', alignItems: 'center' },
  sectionLabel:  { fontSize: 11, fontWeight: '700', color: COLORS.muted, textTransform: 'uppercase', letterSpacing: 1.1, marginBottom: 10 },
  emptyCard:     { backgroundColor: COLORS.card, borderRadius: 12, padding: 16, marginBottom: 20, borderWidth: 1, borderColor: COLORS.border },
  emptyText:     { fontSize: 13, color: COLORS.muted, lineHeight: 19 },
  creditCard:    { backgroundColor: COLORS.card, borderRadius: 12, padding: 14, marginBottom: 8, flexDirection: 'row', alignItems: 'center', borderWidth: 1, borderColor: COLORS.border },
  creditName:    { fontSize: 15, fontWeight: '700', color: COLORS.text },
  creditCount:   { fontSize: 13, color: COLORS.primary, fontWeight: '600', marginTop: 2 },
  adjRow:        { flexDirection: 'row', gap: 8 },
  adjBtn:        { backgroundColor: COLORS.danger, borderRadius: 8, width: 32, height: 32, alignItems: 'center', justifyContent: 'center' },
  adjBtnText:    { color: '#fff', fontSize: 18, fontWeight: '700', lineHeight: 22 },
  slotHeader:    { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 8, marginBottom: 10 },
  addBtn:        { backgroundColor: COLORS.primary, borderRadius: 8, paddingVertical: 6, paddingHorizontal: 14 },
  addBtnText:    { color: '#fff', fontWeight: '700', fontSize: 13 },
  slotCard:      { backgroundColor: COLORS.card, borderRadius: 12, padding: 14, marginBottom: 8, flexDirection: 'row', alignItems: 'center', borderWidth: 1, borderColor: COLORS.border },
  slotDate:      { fontSize: 15, fontWeight: '700', color: COLORS.text },
  slotTime:      { fontSize: 13, color: COLORS.subtext, marginTop: 2 },
  slotNote:      { fontSize: 12, color: COLORS.muted, marginTop: 4 },
  bookedBadge:   { fontSize: 12, color: COLORS.success, fontWeight: '600', marginTop: 4 },
  deleteBtn:     { fontSize: 20, color: COLORS.danger, fontWeight: '700', padding: 4 },
  modalBackdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)' },
  modalSheet:    { backgroundColor: COLORS.card, borderTopLeftRadius: 20, borderTopRightRadius: 20, padding: 24, paddingBottom: 40 },
  modalTitle:    { fontSize: 18, fontWeight: '800', color: COLORS.text, marginBottom: 16 },
  modalLabel:    { fontSize: 12, fontWeight: '700', color: COLORS.muted, marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.8 },
  input:         { backgroundColor: COLORS.bg, borderWidth: 1.5, borderColor: COLORS.border, borderRadius: 10, padding: 12, fontSize: 15, color: COLORS.text, marginBottom: 14 },
  saveBtn:       { backgroundColor: COLORS.primary, borderRadius: 12, height: 50, alignItems: 'center', justifyContent: 'center', marginTop: 4 },
  saveBtnText:   { color: '#fff', fontWeight: '700', fontSize: 15 },
});
