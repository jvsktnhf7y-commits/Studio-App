import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  Alert, ActivityIndicator, RefreshControl,
} from 'react-native';
import { parentGetMakeupCredits, parentGetMakeupSlots, parentBookMakeup } from '../../services/api';
import { COLORS } from '../../theme';

function formatSlotDate(dateStr) {
  try {
    const d = new Date(dateStr + 'T12:00:00');
    return d.toLocaleDateString([], { weekday: 'long', month: 'short', day: 'numeric' });
  } catch { return dateStr; }
}

export default function ParentMakeupScreen() {
  const [credits,    setCredits]    = useState(0);
  const [slots,      setSlots]      = useState([]);
  const [loading,    setLoading]    = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [booking,    setBooking]    = useState(null);

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true); else setLoading(true);
    try {
      const [c, s] = await Promise.all([parentGetMakeupCredits(), parentGetMakeupSlots()]);
      if (c.ok) setCredits(c.credits);
      if (s.ok) setSlots(s.slots);
    } catch { Alert.alert('Error', 'Could not load make-up info.'); }
    finally { setLoading(false); setRefreshing(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleBook(slot) {
    if (credits <= 0) {
      Alert.alert('No credits', 'You have no make-up credits to use.');
      return;
    }
    Alert.alert(
      'Book make-up lesson',
      `${formatSlotDate(slot.date)} at ${slot.time} (${slot.duration} min)${slot.note ? '\n' + slot.note : ''}`,
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Book it', onPress: async () => {
          setBooking(slot.id);
          try {
            const res = await parentBookMakeup(slot.id);
            if (res.ok) {
              setCredits(res.credits_remaining);
              setSlots(prev => prev.filter(s => s.id !== slot.id));
              Alert.alert('Booked!', `Your make-up lesson is confirmed for ${formatSlotDate(slot.date)} at ${slot.time}.`);
            } else {
              Alert.alert('Could not book', res.error || 'Please try again.');
            }
          } catch { Alert.alert('Error', 'Something went wrong.'); }
          finally { setBooking(null); }
        }},
      ]
    );
  }

  if (loading) return <View style={styles.center}><ActivityIndicator size="large" color={COLORS.primary} /></View>;

  return (
    <View style={styles.container}>
      <View style={styles.creditBanner}>
        <Text style={styles.creditCount}>{credits}</Text>
        <Text style={styles.creditLabel}>Make-up credit{credits !== 1 ? 's' : ''} available</Text>
        <Text style={styles.creditHint}>
          {credits > 0 ? 'Pick an available slot below to book.' : 'Credits are issued when a lesson is missed or cancelled.'}
        </Text>
      </View>

      {slots.length === 0 ? (
        <View style={styles.empty}>
          <Text style={styles.emptyIcon}>📭</Text>
          <Text style={styles.emptyTitle}>No slots open yet</Text>
          <Text style={styles.emptyText}>Your teacher will post available times here. You'll get a notification when one opens up.</Text>
        </View>
      ) : (
        <FlatList
          data={slots}
          keyExtractor={s => s.id}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={COLORS.primary} />}
          contentContainerStyle={{ padding: 16, paddingBottom: 40 }}
          renderItem={({ item }) => (
            <View style={styles.slotCard}>
              <View style={{ flex: 1 }}>
                <Text style={styles.slotDate}>{formatSlotDate(item.date)}</Text>
                <Text style={styles.slotTime}>{item.time} · {item.duration} min</Text>
                {!!item.note && <Text style={styles.slotNote}>{item.note}</Text>}
              </View>
              <TouchableOpacity
                style={[styles.bookBtn, (credits <= 0 || booking === item.id) && styles.bookBtnDisabled]}
                onPress={() => handleBook(item)}
                disabled={credits <= 0 || !!booking}
                activeOpacity={0.75}
              >
                {booking === item.id
                  ? <ActivityIndicator size="small" color="#fff" />
                  : <Text style={styles.bookBtnText}>{credits > 0 ? 'Book' : 'No credits'}</Text>
                }
              </TouchableOpacity>
            </View>
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container:       { flex: 1, backgroundColor: COLORS.bg },
  center:          { flex: 1, justifyContent: 'center', alignItems: 'center' },
  creditBanner:    { backgroundColor: COLORS.card, borderBottomWidth: 1, borderBottomColor: COLORS.border, padding: 20, alignItems: 'center' },
  creditCount:     { fontSize: 52, fontWeight: '800', color: COLORS.primary },
  creditLabel:     { fontSize: 15, fontWeight: '700', color: COLORS.text, marginBottom: 4 },
  creditHint:      { fontSize: 13, color: COLORS.muted, textAlign: 'center', lineHeight: 18 },
  empty:           { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 40 },
  emptyIcon:       { fontSize: 48, marginBottom: 12 },
  emptyTitle:      { fontSize: 18, fontWeight: '800', color: COLORS.text, marginBottom: 6 },
  emptyText:       { fontSize: 14, color: COLORS.muted, textAlign: 'center', lineHeight: 20 },
  slotCard:        { backgroundColor: COLORS.card, borderRadius: 14, padding: 16, marginBottom: 10, flexDirection: 'row', alignItems: 'center', borderWidth: 1, borderColor: COLORS.border },
  slotDate:        { fontSize: 15, fontWeight: '700', color: COLORS.text, marginBottom: 2 },
  slotTime:        { fontSize: 13, color: COLORS.subtext, fontWeight: '600' },
  slotNote:        { fontSize: 12, color: COLORS.muted, marginTop: 4 },
  bookBtn:         { backgroundColor: COLORS.primary, borderRadius: 10, paddingVertical: 10, paddingHorizontal: 18 },
  bookBtnDisabled: { backgroundColor: COLORS.muted },
  bookBtnText:     { color: '#fff', fontWeight: '700', fontSize: 14 },
});
