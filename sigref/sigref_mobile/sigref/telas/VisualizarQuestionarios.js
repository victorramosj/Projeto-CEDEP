import React, { useState, useEffect, useCallback } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ActivityIndicator, 
  ScrollView, 
  RefreshControl,
  TouchableOpacity,
  Alert,
  FlatList, // Para a lista de questionários
  Button // Para o botão de relatório
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import axios from 'axios';
import { useRoute, useNavigation } from '@react-navigation/native';
import { format, parseISO, formatDistanceToNowStrict } from 'date-fns';
import { ptBR } from 'date-fns/locale';

// URL base da sua API Django
const API_BASE_URL = 'http://10.0.2.2:8000'; // para emulador android

// Chave para o cache do AsyncStorage
const QUESTIONARIOS_ESCOLA_CACHE_KEY = '@questionarios_escola_cache_'; 

const QuestionariosEscolaScreen = () => {
  const route = useRoute();
  const navigation = useNavigation();
  const { escolaId, userData } = route.params; // Recebe escolaId e userData

  const [screenData, setScreenData] = useState(null); // Dados da tela (escola, questionários, stats)
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [isOffline, setIsOffline] = useState(false);

  // Função para carregar dados do cache
  const loadDataFromCache = useCallback(async () => {
    try {
      const cachedData = await AsyncStorage.getItem(`${QUESTIONARIOS_ESCOLA_CACHE_KEY}${escolaId}`);
      if (cachedData) {
        setScreenData(JSON.parse(cachedData));
        console.log('Dados de questionários da escola carregados do cache.');
      } else {
        console.log('Nenhum dado de questionários da escola encontrado no cache.');
      }
    } catch (e) {
      console.error('Erro ao carregar dados do cache:', e);
    }
  }, [escolaId]);

  // Função para buscar dados da API
  const fetchData = useCallback(async (showAlert = true) => {
    setRefreshing(true);
    try {
      const netInfoState = await NetInfo.fetch();
      setIsOffline(!netInfoState.isConnected);

      if (!netInfoState.isConnected) {
        if (showAlert) {
          Alert.alert('Modo Offline', 'Você está offline. Exibindo dados em cache. Conecte-se à internet para atualizar.');
        }
        return;
      }

      const token = userData?.token;
      if (!token) {
        Alert.alert('Erro de Autenticação', 'Token de autenticação não encontrado. Por favor, faça login novamente.');
        navigation.replace('Login');
        return;
      }

      const url = `${API_BASE_URL}/monitoramento/api/escola/${escolaId}/questionarios/`;
      const response = await axios.get(url, {
        headers: { 'Authorization': `Token ${token}` }
      });
      
      setScreenData(response.data);
      await AsyncStorage.setItem(`${QUESTIONARIOS_ESCOLA_CACHE_KEY}${escolaId}`, JSON.stringify(response.data));
      console.log('Dados de questionários da escola atualizados da API e salvos no cache.');

    } catch (error) {
      console.error('Erro ao buscar questionários da escola:', error);
      if (error.response && (error.response.status === 403 || error.response.status === 401)) {
        Alert.alert('Acesso Negado', 'Você não tem permissão para acessar esta funcionalidade ou sua sessão expirou. Por favor, faça login novamente.');
        navigation.replace('Login');
      } else {
        Alert.alert('Erro', 'Não foi possível carregar os questionários. Verifique a conexão ou tente novamente.');
      }
      setIsOffline(true);
    } finally {
      setRefreshing(false);
      setLoading(false); // Desativa o loading mesmo em caso de erro
    }
  }, [escolaId, userData, navigation]);

  useEffect(() => {
    setLoading(true);
    loadDataFromCache().then(() => {
      fetchData(false); 
    });
  }, [loadDataFromCache, fetchData]);

  const onRefresh = useCallback(() => {
    fetchData(true);
  }, [fetchData]);

  const handleResponderQuestionario = (questionarioId) => {
    navigation.navigate('ResponderQuestionario', { 
      escolaId: escolaId, 
      questionarioId: questionarioId, 
      userData: userData 
    });
  };

  const handleGerarRelatorioDiario = () => {
    Alert.alert('Gerar Relatório Diário', 'Funcionalidade de geração de relatório diário será implementada.');
    // navigation.navigate('RelatorioDiario', { escolaId: escolaId, userData: userData });
  };

  if (loading || !screenData) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#0000ff" />
        <Text style={styles.loadingText}>Carregando questionários...</Text>
      </View>
    );
  }

  const escola = screenData.escola;
  const questionarios = screenData.questionarios;
  const meusMonitoramentosHoje = screenData.meus_monitoramentos_hoje;
  const meusMonitoramentosTotal = screenData.meus_monitoramentos_total;
  const setoresRespondidos = screenData.setores_respondidos;
  const questionariosRespondidos = screenData.questionarios_respondidos;
  const totalHoje = screenData.total_hoje;
  const totalGeral = screenData.total_geral;
  const ultimaRespostaGeral = screenData.ultima_resposta_geral;
  const hoje = screenData.hoje;
  const userIsMonitor = screenData.user_is_monitor;

  // Lógica de validação de relatório
  const MIN_MONITORAMENTOS_VALIDOS = 5;
  const isRelatorioValido = meusMonitoramentosTotal >= MIN_MONITORAMENTOS_VALIDOS;
  const faltamMonitoramentos = MIN_MONITORAMENTOS_VALIDOS - meusMonitoramentosTotal;

  const renderQuestionarioCard = ({ item: questionario, index }) => ( // Adicionado index para o número
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <Text style={styles.cardTitle}>{questionario.titulo}</Text>
        <Text style={styles.badge}>{index + 1}</Text> {/* Usando index + 1 para a numeração */}
      </View>
      <View style={styles.cardBody}>
        <Text style={styles.cardText}>{questionario.descricao || "Sem descrição"}</Text>
        <View style={styles.statsContainer}>
          <View style={styles.badgeInfo}>
            <Text style={styles.badgeText}>Hoje: {questionario.respostas_hoje}</Text>
          </View>
          <View style={styles.badgeSecondary}>
            <Text style={styles.badgeText}>Total: {questionario.total_respostas}</Text>
          </View>
        </View>
        <View style={styles.progressBarBackground}>
          <View style={[styles.progressBarFill, { width: `${(questionario.respostas_hoje / questionario.total_respostas) * 100 || 0}%` }]} />
        </View>
      </View>
      <View style={styles.cardFooter}>
        <Text style={styles.lastResponseText}>
          {questionario.ultima_resposta_criado_em 
            ? `${formatDistanceToNowStrict(parseISO(questionario.ultima_resposta_criado_em), { addSuffix: true, locale: ptBR })}` 
            : 'Nunca respondido'}
        </Text>
        <TouchableOpacity 
          style={styles.responderButton}
          onPress={() => handleResponderQuestionario(questionario.id)}
        >
          <Text style={styles.responderButtonText}>Responder</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <ScrollView 
      style={styles.container}
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

      <View style={styles.headerSection}>
        <View>
          <Text style={styles.headerSchoolName}>{escola.nome}</Text>
          <Text style={styles.headerSubtitle}>Questionários disponíveis para resposta</Text>
        </View>
        <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
          <Text style={styles.backButtonText}>Voltar</Text>
        </TouchableOpacity>
      </View>

      {userIsMonitor && (
        <View style={styles.myActivityCard}>
          <Text style={styles.myActivityTitle}>Minha Atividade</Text>
          <View style={styles.myActivityStatsRow}>
            <View style={styles.myActivityStatItem}>
              <Text style={styles.myActivityStatValue}>{meusMonitoramentosHoje}</Text>
              <Text style={styles.myActivityStatText}>Minhas respostas hoje</Text>
            </View>
            <View style={styles.myActivityStatItem}>
              <Text style={styles.myActivityStatValue}>{meusMonitoramentosTotal}</Text>
              <Text style={styles.myActivityStatText}>Minhas respostas totais</Text>
            </View>
            <View style={styles.myActivityStatItem}>
              <TouchableOpacity style={styles.generateReportButton} onPress={handleGerarRelatorioDiario}>
                <Text style={styles.generateReportButtonText}>Gerar Relatório Diário</Text>
              </TouchableOpacity>
            </View>
          </View>

          {(setoresRespondidos.length > 0 || questionariosRespondidos.length > 0) && (
            <View style={styles.myActivityDetailsRow}>
              {setoresRespondidos.length > 0 && (
                <View style={styles.myActivityDetailCol}>
                  <Text style={styles.myActivityDetailTitle}>Setores que você já monitorou:</Text>
                  <View style={styles.badgesContainer}>
                    {setoresRespondidos.map(setor => (
                      <Text key={setor.id} style={styles.badgeSuccess}>{setor.hierarquia_completa}</Text>
                    ))}
                  </View>
                </View>
              )}
              {questionariosRespondidos.length > 0 && (
                <View style={styles.myActivityDetailCol}>
                  <Text style={styles.myActivityDetailTitle}>Questionários que você já respondeu:</Text>
                  <View style={styles.badgesContainer}>
                    {questionariosRespondidos.map(q => (
                      <Text key={q.id} style={styles.badgePrimary}>{q.titulo.substring(0, 25)}{q.titulo.length > 25 ? '...' : ''}</Text>
                    ))}
                  </View>
                </View>
              )}
            </View>
          )}

          <View style={[styles.validationAlert, isRelatorioValido ? styles.alertSuccess : styles.alertWarning]}>
            <Text style={styles.validationAlertTitle}>Validação de Relatório</Text>
            <Text style={styles.validationAlertText}>
              Para que seu relatório seja considerado válido, é necessário realizar
              pelo menos <Text style={styles.boldText}>5 monitoramentos</Text> em diferentes setores.
              {!isRelatorioValido ? (
                ` Você já fez ${meusMonitoramentosTotal} - faltam ${faltamMonitoramentos}.`
              ) : (
                ` Parabéns! Você já completou o mínimo necessário.`
              )}
            </Text>
          </View>
        </View>
      )}

      <View style={styles.generalSummaryCard}>
        <Text style={styles.generalSummaryTitle}>Resumo Geral da Escola</Text>
        <View style={styles.generalSummaryStatsRow}>
          <View style={styles.generalSummaryStatItem}>
            <Text style={styles.generalSummaryStatValue}>{totalHoje}</Text>
            <Text style={styles.generalSummaryStatText}>Hoje ({format(parseISO(hoje), 'dd/MM/yyyy', { locale: ptBR })})</Text>
          </View>
          <View style={styles.generalSummaryStatItem}>
            <Text style={styles.generalSummaryStatValue}>{totalGeral}</Text>
            <Text style={styles.generalSummaryStatText}>Total de Respostas</Text>
          </View>
          <View style={styles.generalSummaryStatItem}>
            <Text style={styles.generalSummaryStatValue}>
              {ultimaRespostaGeral ? (
                <>
                  <Text>{format(parseISO(ultimaRespostaGeral), 'dd/MM/yyyy', { locale: ptBR })}</Text>
                  {'\n'}
                  <Text>{format(parseISO(ultimaRespostaGeral), 'HH:mm', { locale: ptBR })}</Text>
                </>
              ) : (
                '--'
              )}
            </Text>
            <Text style={styles.generalSummaryStatText}>Último registro</Text>
          </View>
        </View>
      </View>

      <Text style={styles.questionariosListTitle}>Questionários Disponíveis</Text>
      <FlatList
        data={questionarios}
        keyExtractor={(item) => item.id.toString()}
        renderItem={renderQuestionarioCard}
        ListEmptyComponent={() => (
          <View style={styles.emptyListContainer}>
            <Text style={styles.emptyListIcon}>&#x1F4CB;</Text>
            <Text style={styles.emptyListText}>Nenhum questionário disponível</Text>
            <Text style={styles.emptyListSmallText}>Esta escola ainda não tem questionários atribuídos</Text>
          </View>
        )}
      />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  contentContainer: {
    padding: 15,
    paddingBottom: 30,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
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
  headerSection: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
    paddingBottom: 10,
  },
  headerSchoolName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#0d6efd',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#6c757d',
  },
  backButton: {
    backgroundColor: '#6c757d',
    paddingVertical: 8,
    paddingHorizontal: 15,
    borderRadius: 8,
  },
  backButtonText: {
    color: 'white',
    fontWeight: 'bold',
  },
  myActivityCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    overflow: 'hidden',
  },
  myActivityTitle: {
    backgroundColor: '#0dcaf0', // bg-info
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
    padding: 15,
    borderTopLeftRadius: 12,
    borderTopRightRadius: 12,
  },
  myActivityStatsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    padding: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  myActivityStatItem: {
    alignItems: 'center',
    flex: 1,
  },
  myActivityStatValue: {
    fontSize: 36, // display-5
    fontWeight: 'bold',
    color: '#0dcaf0', // text-info
    marginBottom: 5,
  },
  myActivityStatText: {
    fontSize: 12,
    color: '#6c757d', // text-muted
    textAlign: 'center',
  },
  generateReportButton: {
    backgroundColor: '#0d6efd', // primary
    paddingVertical: 10,
    paddingHorizontal: 15,
    borderRadius: 8,
    marginTop: 10,
  },
  generateReportButtonText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 14,
  },
  myActivityDetailsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 15,
  },
  myActivityDetailCol: {
    width: '100%', // Uma coluna em mobile
    marginBottom: 10,
  },
  myActivityDetailTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  badgesContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 5,
  },
  badgeSuccess: {
    backgroundColor: '#28a745', // bg-success
    color: 'white',
    paddingVertical: 5,
    paddingHorizontal: 10,
    borderRadius: 8,
    fontSize: 12,
    fontWeight: 'bold',
  },
  badgePrimary: {
    backgroundColor: '#0d6efd', // bg-primary
    color: 'white',
    paddingVertical: 5,
    paddingHorizontal: 10,
    borderRadius: 8,
    fontSize: 12,
    fontWeight: 'bold',
  },
  validationAlert: {
    padding: 15,
    borderRadius: 8,
    marginTop: 10,
    flexDirection: 'row',
    alignItems: 'center',
  },
  alertWarning: {
    backgroundColor: '#fff3cd', // alert-warning
    borderColor: '#ffeeba',
    borderWidth: 1,
  },
  alertSuccess: {
    backgroundColor: '#d4edda', // alert-success
    borderColor: '#c3e6cb',
    borderWidth: 1,
  },
  validationAlertTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  validationAlertText: {
    fontSize: 14,
    color: '#333',
  },
  boldText: {
    fontWeight: 'bold',
  },
  generalSummaryCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    overflow: 'hidden',
  },
  generalSummaryTitle: {
    backgroundColor: '#0d6efd', // bg-primary
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
    padding: 15,
    borderTopLeftRadius: 12,
    borderTopRightRadius: 12,
  },
  generalSummaryStatsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    padding: 15,
  },
  generalSummaryStatItem: {
    alignItems: 'center',
    flex: 1,
  },
  generalSummaryStatValue: {
    fontSize: 36, // display-5
    fontWeight: 'bold',
    color: '#0d6efd', // text-primary
    marginBottom: 5,
  },
  generalSummaryStatText: {
    fontSize: 12,
    color: '#6c757d', // text-muted
    textAlign: 'center',
  },
  questionariosListTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
    borderBottomWidth: 3,
    borderBottomColor: '#0d6efd',
    paddingBottom: 5,
    alignSelf: 'flex-start', // Para que a borda seja apenas no texto
  },
  card: {
    backgroundColor: 'white',
    borderRadius: 12,
    marginBottom: 15,
    borderLeftWidth: 4,
    borderLeftColor: '#0d6efd',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    overflow: 'hidden',
  },
  cardHeader: {
    backgroundColor: '#f8f9fa', // bg-light
    padding: 15,
    borderTopLeftRadius: 8,
    borderTopRightRadius: 8,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    flexShrink: 1, // Permite que o título quebre linha
    marginRight: 10,
  },
  badge: {
    backgroundColor: '#6c757d',
    color: 'white',
    paddingVertical: 5,
    paddingHorizontal: 10,
    borderRadius: 8,
    fontSize: 12,
    fontWeight: 'bold',
  },
  cardBody: {
    padding: 15,
  },
  cardText: {
    fontSize: 14,
    color: '#6c757d',
    marginBottom: 10,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  badgeInfo: {
    backgroundColor: '#0dcaf0',
    color: 'white',
    paddingVertical: 5,
    paddingHorizontal: 10,
    borderRadius: 8,
    fontSize: 12,
    fontWeight: 'bold',
  },
  badgeSecondary: {
    backgroundColor: '#6c757d',
    color: 'white',
    paddingVertical: 5,
    paddingHorizontal: 10,
    borderRadius: 8,
    fontSize: 12,
    fontWeight: 'bold',
  },
  progressBarBackground: {
    height: 8,
    backgroundColor: '#e9ecef',
    borderRadius: 10,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: '#0dcaf0', // bg-info
    borderRadius: 10,
  },
  cardFooter: {
    padding: 15,
    borderTopWidth: 1,
    borderTopColor: '#eee',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  lastResponseText: {
    fontSize: 12,
    color: '#6c757d',
  },
  responderButton: {
    backgroundColor: '#28a745', // bg-success
    paddingVertical: 8,
    paddingHorizontal: 15,
    borderRadius: 50, // rounded-pill
  },
  responderButtonText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 14,
  },
  emptyListContainer: {
    alignItems: 'center',
    paddingVertical: 50,
  },
  emptyListIcon: {
    fontSize: 60,
    color: '#6c757d',
    marginBottom: 15,
  },
  emptyListText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#6c757d',
    marginBottom: 5,
  },
  emptyListSmallText: {
    fontSize: 14,
    color: '#6c757d',
    textAlign: 'center',
  },
});

export default QuestionariosEscolaScreen;
