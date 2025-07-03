import React, { useState, useEffect, useCallback } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ActivityIndicator, 
  ScrollView, 
  RefreshControl,
  Alert,
  Modal,
  TouchableOpacity 
} from 'react-native';
import { Calendar, LocaleConfig } from 'react-native-calendars';
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import axios from 'axios';
import { format, parseISO } from 'date-fns';
import { ptBR } from 'date-fns/locale';

// Configuração do Locale para react-native-calendars
LocaleConfig.locales['pt-br'] = {
  monthNames: [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
  ],
  monthNamesShort: ['Jan.', 'Fev.', 'Mar.', 'Abr.', 'Mai.', 'Jun.', 'Jul.', 'Ago.', 'Set.', 'Out.', 'Nov.', 'Dez.'],
  dayNames: ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado'],
  dayNamesShort: ['Dom.', 'Seg.', 'Ter.', 'Qua.', 'Qui.', 'Sex.', 'Sáb.'],
  today: 'Hoje'
};
LocaleConfig.defaultLocale = 'pt-br';

// Constantes para chaves do AsyncStorage
const CALENDAR_EVENTS_CACHE_KEY = '@calendar_events_cache';

// URL base da sua API Django
// const API_BASE_URL = 'http://127.0.0.1:8000'; //para pc
const API_BASE_URL = 'http://10.0.2.2:8000'; //para emulador android
//const API_BASE_URL = 'https://grefloresta.com.br';  URL do servidor remoto

const CalendarScreen = () => {
  const [events, setEvents] = useState({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [isOffline, setIsOffline] = useState(false);
  const [showEventModal, setShowEventModal] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState(null);

  // Função para carregar dados do cache
  const loadFromCache = useCallback(async () => {
    try {
      const cachedEvents = await AsyncStorage.getItem(CALENDAR_EVENTS_CACHE_KEY);
      if (cachedEvents) {
        setEvents(JSON.parse(cachedEvents));
      }
    } catch (e) {
      console.error('Erro ao carregar eventos do cache:', e);
    }
  }, []);

  // Função para buscar dados da API
  const fetchEvents = useCallback(async () => {
    try {
      const netInfoState = await NetInfo.fetch();
      setIsOffline(!netInfoState.isConnected);

      if (!netInfoState.isConnected) {
        Alert.alert('Modo Offline', 'Você está offline. Exibindo dados em cache. Conecte-se à internet para atualizar.');
        return;
      }

      const eventsResponse = await axios.get(`${API_BASE_URL}/eventos/api/fullcalendar/`);
      const rawEvents = eventsResponse.data;

      const formattedEvents = {};
      rawEvents.forEach(event => {
        const date = format(parseISO(event.start), 'yyyy-MM-dd');
        if (!formattedEvents[date]) {
          formattedEvents[date] = [];
        }
        formattedEvents[date].push({
          id: event.id,
          title: event.title,
          start: event.start,
          end: event.end,
          horario: event.extendedProps.horario,
          salas: event.extendedProps.salas,
          organizador: event.extendedProps.organizador,
          descricao: event.extendedProps.descricao,
        });
      });
      setEvents(formattedEvents);
      await AsyncStorage.setItem(CALENDAR_EVENTS_CACHE_KEY, JSON.stringify(formattedEvents));

    } catch (error) {
      console.error('Erro ao buscar eventos da API:', error);
      Alert.alert('Erro', 'Não foi possível carregar os eventos. Verifique a conexão ou tente novamente.');
      setIsOffline(true);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    loadFromCache().then(() => {
      fetchEvents();
    });
  }, [loadFromCache, fetchEvents]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchEvents();
  }, [fetchEvents]);

  // Função para abrir o modal do evento
  const handleEventPress = (event) => {
    setSelectedEvent(event);
    setShowEventModal(true);
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#0000ff" />
        <Text style={styles.loadingText}>Carregando calendário...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView 
        contentContainerStyle={styles.contentContainer}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {isOffline && (
          <View style={styles.offlineBanner}>
            <Text style={styles.offlineText}>Você está offline. Dados podem estar desatualizados.</Text>
          </View>
        )}

        {/* Calendário */}
        <View style={styles.calendarContainer}>
          <Calendar
            markedDates={
              Object.keys(events).reduce((acc, date) => {
                acc[date] = { marked: true, dotColor: '#2196F3' }; 
                return acc;
              }, {})
            }
            onDayPress={(day) => {
              const dayEvents = events[day.dateString];
              if (dayEvents && dayEvents.length > 0) {
                setSelectedEvent({ isDaySummary: true, date: day.dateString, events: dayEvents });
                setShowEventModal(true);
              } else {
                console.log('Dia selecionado (sem eventos):', day);
              }
            }}
            renderArrow={(direction) => (
              <Text style={styles.arrowButton}>{direction === 'left' ? '<' : '>'}</Text>
            )}
            dayComponent={({ date, state, marking }) => {
              const dayEvents = events[date.dateString];
              return (
                <View style={styles.dayContainer}>
                  <Text style={[styles.dayText, state === 'disabled' ? styles.disabledText : {}]}>
                    {date.day}
                  </Text>
                  {marking && marking.marked && <View style={styles.dot} />}
                  
                  {dayEvents && dayEvents.length > 0 && (
                    <View style={styles.eventsContainer}>
                      {dayEvents.slice(0, 2).map((event, index) => (
                        <TouchableOpacity 
                          key={event.id || index}
                          style={styles.eventItem}
                          onPress={() => handleEventPress(event)}
                        >
                          <Text style={styles.eventTitle} numberOfLines={1}>{event.title}</Text>
                          <Text style={styles.eventHorario}>{event.horario}</Text>
                        </TouchableOpacity>
                      ))}
                      {dayEvents.length > 2 && (
                        <Text style={styles.moreEventsText}>+{dayEvents.length - 2} eventos</Text>
                      )}
                    </View>
                  )}
                </View>
              );
            }}
            theme={{
              calendarBackground: '#ffffff',
              textSectionTitleColor: '#b6c1cd',
              selectedDayBackgroundColor: '#00adf5',
              selectedDayTextColor: '#ffffff',
              todayTextColor: '#00adf5',
              dayTextColor: '#2d4150',
              textDisabledColor: '#d9e1e8',
              dotColor: '#00adf5',
              selectedDotColor: '#ffffff',
              arrowColor: '#00adf5',
              monthTextColor: '#00adf5',
              textMonthFontWeight: 'bold',
              textDayHeaderFontWeight: 'bold',
              textDayFontSize: 16,
              textMonthFontSize: 18,
              textDayHeaderFontSize: 14,
              'stylesheet.calendar.main': {
                container: {
                  padding: 0,
                }
              },
              'stylesheet.day.basic': {
                base: {
                  width: 32,
                  height: 32,
                  alignItems: 'center',
                  justifyContent: 'center',
                }
              }
            }}
            fixedWeekCount={false}
          />
        </View>
      </ScrollView>

      {/* Modal de Detalhes do Evento */}
      <Modal
        animationType="fade"
        transparent={true}
        visible={showEventModal}
        onRequestClose={() => {
          setShowEventModal(false);
          setSelectedEvent(null);
        }}
      >
        <View style={styles.centeredView}>
          <View style={styles.modalView}>
            {selectedEvent && selectedEvent.isDaySummary ? (
              // Conteúdo para o resumo do dia
              <ScrollView style={{ maxHeight: 400 }}>
                <Text style={styles.modalTitle}>Eventos em {format(parseISO(selectedEvent.date), 'dd/MM/yyyy', { locale: ptBR })}</Text>
                {selectedEvent.events.map((event, index) => (
                  <View key={event.id || index} style={styles.modalEventItem}>
                    <Text style={styles.modalEventTitle}>{event.title}</Text>
                    <Text style={styles.modalEventDetail}>Horário: {event.horario}</Text>
                    {event.salas && event.salas.length > 0 && (
                      <Text style={styles.modalEventDetail}>Salas: {event.salas.join(', ')}</Text>
                    )}
                    {event.organizador && (
                      <Text style={styles.modalEventDetail}>Organizador: {event.organizador}</Text>
                    )}
                    {event.descricao && (
                      <Text style={styles.modalEventDetail}>Descrição: {event.descricao}</Text>
                    )}
                  </View>
                ))}
              </ScrollView>
            ) : (
              // Conteúdo para um único evento
              selectedEvent && (
                <ScrollView style={{ maxHeight: 400 }}>
                  <Text style={styles.modalTitle}>{selectedEvent.title}</Text>
                  <Text style={styles.modalText}>Horário: {selectedEvent.horario}</Text>
                  {selectedEvent.salas && selectedEvent.salas.length > 0 && (
                    <Text style={styles.modalText}>Salas: {selectedEvent.salas.join(', ')}</Text>
                  )}
                  {selectedEvent.organizador && (
                    <Text style={styles.modalText}>Organizador: {selectedEvent.organizador}</Text>
                  )}
                  {selectedEvent.descricao && (
                    <Text style={styles.modalText}>Descrição: {selectedEvent.descricao}</Text>
                  )}
                </ScrollView>
              )
            )}
            <TouchableOpacity
              style={styles.buttonClose}
              onPress={() => {
                setShowEventModal(false);
                setSelectedEvent(null);
              }}
            >
              <Text style={styles.textStyle}>Fechar</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  contentContainer: {
    padding: 10,
    paddingBottom: 30,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#333',
  },
  offlineBanner: {
    backgroundColor: '#ffcc00',
    padding: 10,
    borderRadius: 8,
    marginBottom: 10,
    alignItems: 'center',
  },
  offlineText: {
    color: '#333',
    fontWeight: 'bold',
  },
  calendarContainer: {
    backgroundColor: '#ffffff',
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    marginBottom: 20,
    overflow: 'hidden',
  },
  arrowButton: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#00adf5',
    paddingHorizontal: 10,
  },
  dayContainer: {
    minHeight: 100, // Altura mínima para cada dia
    padding: 4,
  },
  dayText: {
    fontSize: 16,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 2,
  },
  disabledText: {
    color: '#ccc',
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#00adf5',
    alignSelf: 'center',
  },
  eventsContainer: {
    marginTop: 4,
  },
  eventItem: {
    backgroundColor: '#e6f7ff',
    borderRadius: 4,
    padding: 3,
    marginVertical: 1,
    borderLeftWidth: 3,
    borderLeftColor: '#2196F3',
  },
  eventTitle: {
    fontSize: 9,
    fontWeight: 'bold',
    color: '#333',
  },
  eventHorario: {
    fontSize: 8,
    color: '#666',
  },
  moreEventsText: {
    fontSize: 8,
    color: '#2196F3',
    textAlign: 'center',
    marginTop: 2,
    fontStyle: 'italic',
  },
  centeredView: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  modalView: {
    margin: 20,
    backgroundColor: 'white',
    borderRadius: 20,
    padding: 25,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
    width: '90%',
    maxHeight: '80%',
  },
  modalTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    marginBottom: 15,
    color: '#333',
    textAlign: 'center',
  },
  modalText: {
    marginBottom: 10,
    textAlign: 'center',
    fontSize: 16,
    color: '#555',
  },
  modalEventItem: {
    backgroundColor: '#f0f8ff',
    borderRadius: 8,
    padding: 10,
    marginBottom: 10,
    borderLeftWidth: 4,
    borderLeftColor: '#007bff',
    width: '100%',
  },
  modalEventTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#007bff',
    marginBottom: 5,
  },
  modalEventDetail: {
    fontSize: 14,
    color: '#444',
    marginBottom: 3,
  },
  buttonClose: {
    backgroundColor: '#2196F3',
    borderRadius: 10,
    padding: 12,
    elevation: 2,
    marginTop: 20,
    width: '60%',
    alignItems: 'center',
  },
  textStyle: {
    color: 'white',
    fontWeight: 'bold',
    textAlign: 'center',
    fontSize: 16,
  },
});

export default CalendarScreen;