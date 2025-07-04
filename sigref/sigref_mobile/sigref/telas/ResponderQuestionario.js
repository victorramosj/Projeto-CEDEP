import React, { useState, useEffect, useCallback } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ActivityIndicator, 
  ScrollView, 
  RefreshControl,
  TouchableOpacity,
  TextInput,
  Alert,
  Button 
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import axios from 'axios';
import { useRoute, useNavigation, useFocusEffect } from '@react-navigation/native';
import { format, parseISO } from 'date-fns';
import { ptBR } from 'date-fns/locale';

// URL base da sua API Django
const API_BASE_URL = 'http://10.0.2.2:8000'; // para emulador android

// Chave para armazenar submissões pendentes
const PENDING_SUBMISSIONS_KEY = '@pending_questionnaire_submissions';
// Nova chave para armazenar os dados do questionário em cache (perguntas)
const QUESTIONARIO_DATA_CACHE_KEY = '@questionario_data_cache_';

const ResponderQuestionarioScreen = () => {
  const route = useRoute();
  const navigation = useNavigation();
  const { escolaId, questionarioId, userData } = route.params;

  const [questionarioData, setQuestionarioData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [isOffline, setIsOffline] = useState(false);
  const [respostas, setRespostas] = useState({});

  // Nova função para carregar dados do questionário do cache
  const loadQuestionarioDataFromCache = useCallback(async () => {
    try {
      const cachedData = await AsyncStorage.getItem(`${QUESTIONARIO_DATA_CACHE_KEY}${questionarioId}`);
      if (cachedData) {
        setQuestionarioData(JSON.parse(cachedData));
        console.log('Dados do questionário carregados do cache.');
      } else {
        // Se não houver dados em cache, inicializa com uma estrutura vazia para permitir a renderização
        setQuestionarioData({
          escola: {}, // Objeto vazio para escola
          questionario: {}, // Objeto vazio para questionário
          perguntas: [], // Array vazio para perguntas
          hoje: new Date().toISOString(), // Data atual como fallback
        });
        console.log('Nenhum dado do questionário encontrado no cache. Inicializando com estrutura vazia.');
      }
    } catch (e) {
      console.error('Erro ao carregar questionário do cache:', e);
      // Em caso de erro no cache, ainda inicializa com uma estrutura vazia
      setQuestionarioData({
        escola: {},
        questionario: {},
        perguntas: [],
        hoje: new Date().toISOString(),
      });
      Alert.alert('Erro no Cache', 'Não foi possível carregar dados do cache. Tente atualizar online.');
    }
  }, [questionarioId]);

  // Função para buscar dados do questionário da API
  const fetchQuestionarioData = useCallback(async (showAlert = true) => {
    setRefreshing(true); // Ativa o refreshing para o RefreshControl
    try {
      const netInfoState = await NetInfo.fetch();
      setIsOffline(!netInfoState.isConnected);

      if (!netInfoState.isConnected) {
        // Se offline, já carregamos do cache. Apenas avisamos se solicitado.
        if (showAlert) {
          Alert.alert('Modo Offline', 'Você está offline. Exibindo dados do questionário do cache. Conecte-se à internet para atualizar.');
        }
        // Não desativa o loading aqui, pois o loading inicial é desativado após o cache.
        // O refreshing será desativado no finally.
        return; // Não tenta buscar da API se estiver offline
      }

      const token = userData?.token;
      if (!token) {
        Alert.alert('Erro de Autenticação', 'Token de autenticação não encontrado. Por favor, faça login novamente.');
        navigation.replace('Login');
        return;
      }

      const url = `${API_BASE_URL}/monitoramento/api/escola/${escolaId}/questionario/${questionarioId}/responder/`;
      const response = await axios.get(url, {
        headers: { 'Authorization': `Token ${token}` }
      });
      
      setQuestionarioData(response.data);
      // Salva os dados do questionário no cache após buscar da API
      await AsyncStorage.setItem(`${QUESTIONARIO_DATA_CACHE_KEY}${questionarioId}`, JSON.stringify(response.data));
      console.log('Questionário carregado da API e salvo no cache.');

    } catch (error) {
      console.error('Erro ao buscar questionário:', error);
      if (error.response && (error.response.status === 403 || error.response.status === 401)) {
        Alert.alert('Acesso Negado', 'Você não tem permissão para acessar este questionário ou sua sessão expirou. Por favor, faça login novamente.');
        navigation.replace('Login');
      } else {
        Alert.alert('Erro', 'Não foi possível carregar o questionário. Verifique a conexão ou tente novamente.');
      }
      setIsOffline(true);
    } finally {
      setRefreshing(false); // Desativa o refreshing no final
      setLoading(false); // Garante que o loading inicial seja desativado
    }
  }, [escolaId, questionarioId, userData, navigation]);

  // Efeito para o carregamento inicial da tela
  useEffect(() => {
    console.log("ResponderQuestionarioScreen: useEffect de inicialização acionado.");
    setLoading(true);
    // PASSO 1: Tenta carregar do cache primeiro (para exibição imediata offline)
    loadQuestionarioDataFromCache().then(() => {
      // PASSO 2: Depois, tenta buscar da rede (para garantir dados atualizados)
      fetchQuestionarioData(false); // Não alerta se offline no início, pois já carregou cache
    });
  }, [loadQuestionarioDataFromCache, fetchQuestionarioData]);

  // useFocusEffect para recarregar dados quando a tela entra em foco (ex: ao voltar de ResponderQuestionarioScreen)
  // Isso garante que, se o usuário voltar para esta tela (por exemplo, após enviar uma resposta),
  // os dados sejam re-buscados para garantir que estejam atualizados.
  useFocusEffect(
    useCallback(() => {
      console.log("ResponderQuestionarioScreen focada. Verificando conexão e atualizando dados.");
      const checkConnectionAndFetchOnFocus = async () => {
        const netInfoState = await NetInfo.fetch();
        if (netInfoState.isConnected) {
          console.log("Online no foco: Forçando atualização da API.");
          fetchQuestionarioData(false); // Força um refresh da API, sem alerta inicial de offline
        } else {
          console.log("Offline no foco: Recarregando do cache.");
          setIsOffline(true); 
          loadQuestionarioDataFromCache(); // Recarrega do cache para o caso de ter voltado de um envio offline
          Alert.alert('Modo Offline', 'Você está offline. Exibindo dados do questionário do cache. Conecte-se à internet para atualizar.');
        }
      };
      checkConnectionAndFetchOnFocus();
      
      return () => {
        console.log("ResponderQuestionarioScreen perdeu o foco.");
      };
    }, [fetchQuestionarioData, loadQuestionarioDataFromCache]) // Inclui fetchData e loadQuestionarioDataFromCache como dependências
  );

  const onRefresh = useCallback(() => {
    console.log("Puxar para atualizar acionado.");
    fetchQuestionarioData(true); // Puxar para atualizar sempre tenta buscar e alerta se offline
  }, [fetchQuestionarioData]);

  const handleRespostaChange = (perguntaId, tipoResposta, value) => {
    setRespostas(prevRespostas => ({
      ...prevRespostas,
      [perguntaId]: { tipo: tipoResposta, valor: value }
    }));
  };

  const handleSubmit = async () => {
    const todasRespondidas = questionarioData.perguntas.every(pergunta => {
      const resposta = respostas[pergunta.id];
      if (!resposta) return false;
      
      if (pergunta.tipo_resposta === 'SN' && (resposta.valor === 'S' || resposta.valor === 'N')) return true;
      if (pergunta.tipo_resposta === 'NU' && (isNaN(parseFloat(resposta.valor)))) return false;
      if (pergunta.tipo_resposta === 'TX' && !resposta.valor.trim()) return false;
      
      return true;
    });

    if (!todasRespondidas) {
      Alert.alert('Erro', 'Por favor, responda todas as perguntas.');
      return;
    }

    setLoading(true); 
    const formattedRespostas = questionarioData.perguntas.map(pergunta => {
      const resposta = respostas[pergunta.id];
      const data = {
        pergunta_id: pergunta.id,
      };
      if (pergunta.tipo_resposta === 'SN') {
        data.resposta_sn = resposta.valor;
      } else if (pergunta.tipo_resposta === 'NU') {
        data.resposta_num = parseFloat(resposta.valor);
      } else if (pergunta.tipo_resposta === 'TX') {
        data.resposta_texto = resposta.valor;
      }
      return data;
    });

    const payload = {
      escola_id: escolaId, 
      questionario_id: questionarioId, 
      respostas: formattedRespostas,
    };

    try {
      const netInfoState = await NetInfo.fetch();
      if (!netInfoState.isConnected) {
        await saveSubmissionOffline(payload);
        Alert.alert('Modo Offline', 'Resposta salva localmente. Será enviada quando você estiver online.');
        navigation.goBack(); 
        return; 
      }

      const token = userData?.token;
      if (!token) {
        Alert.alert('Erro de Autenticação', 'Token de autenticação não encontrado. Por favor, faça login novamente.');
        navigation.replace('Login');
        return;
      }

      const url = `${API_BASE_URL}/monitoramento/api/escola/${escolaId}/questionario/${questionarioId}/responder/`;
      const response = await axios.post(url, payload, {
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        }
      });

      if (response.data.status === 'success') {
        Alert.alert('Sucesso', 'Questionário respondido com sucesso!');
        navigation.goBack(); 
      } else {
        Alert.alert('Erro', response.data.message || 'Falha ao enviar questionário.');
      }

    } catch (error) {
      console.error('Erro ao enviar questionário:', error.response?.data || error.message);
      if (error.request) { // Erro de rede/offline
        await saveSubmissionOffline(payload);
        Alert.alert('Modo Offline', 'Falha na conexão. Resposta salva localmente. Será enviada quando você estiver online.');
      } else if (error.response && (error.response.status === 401 || error.response.status === 403)) {
         Alert.alert('Erro de Autenticação/Permissão', 'Sua sessão expirou ou você não tem permissão. Faça login novamente.');
         navigation.replace('Login');
      }
      else {
        Alert.alert('Erro', error.response?.data?.message || 'Não foi possível enviar o questionário. Tente novamente.');
      }
    } finally {
      setLoading(false);
    }
  };

  const saveSubmissionOffline = async (submissionPayload) => {
    try {
      const existingSubmissionsString = await AsyncStorage.getItem(PENDING_SUBMISSIONS_KEY);
      const existingSubmissions = existingSubmissionsString ? JSON.parse(existingSubmissionsString) : [];
      
      const newSubmission = {
        id: Date.now().toString(), 
        timestamp: new Date().toISOString(),
        payload: submissionPayload,
        token: userData?.token 
      };

      const updatedSubmissions = [...existingSubmissions, newSubmission];
      await AsyncStorage.setItem(PENDING_SUBMISSIONS_KEY, JSON.stringify(updatedSubmissions));
      console.log('Submissão salva offline:', newSubmission.id);
    } catch (e) {
      console.error('Erro ao salvar submissão offline:', e);
      Alert.alert('Erro', 'Não foi possível salvar a resposta offline.');
    }
  };

  if (loading || !questionarioData || !questionarioData.perguntas) { // Adicionado !questionarioData.perguntas
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#0000ff" />
        <Text style={styles.loadingText}>Carregando questionário...</Text>
      </View>
    );
  }

  const escola = questionarioData.escola;
  const questionario = questionarioData.questionario;
  const perguntas = questionarioData.perguntas;

  const answeredQuestionsCount = perguntas.filter(pergunta => {
    const resposta = respostas[pergunta.id];
    if (!resposta) return false;
    
    if (pergunta.tipo_resposta === 'SN' && (resposta.valor === 'S' || resposta.valor === 'N')) return true;
    if (pergunta.tipo_resposta === 'NU' && !isNaN(parseFloat(resposta.valor))) return true;
    if (pergunta.tipo_resposta === 'TX' && resposta.valor.trim()) return true;
    
    return false;
  }).length;
  const totalQuestions = perguntas.length;
  const progressPercentage = (answeredQuestionsCount / totalQuestions) * 100;

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
            <Text style={styles.offlineText}>Você está offline. Não é possível enviar respostas.</Text>
          </View>
        )}

        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerInfo}>
            <Text style={styles.headerTitle}>Responder Questionário</Text>
            <Text style={styles.headerSubtitle}>{escola.nome}</Text>
            <Text style={styles.headerDate}>{format(parseISO(questionarioData.hoje), 'dd/MM/yyyy', { locale: ptBR })}</Text>
          </View>
          <Text style={styles.questionarioTitle}>{questionario.titulo}</Text>
          <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
            <Text style={styles.backButtonText}>Voltar</Text>
          </TouchableOpacity>
        </View>

        {/* Progress Bar */}
        <View style={styles.progressContainer}>
          <View style={styles.progressTextContainer}>
            <Text>Progresso</Text>
            <Text>{answeredQuestionsCount}/{totalQuestions}</Text>
          </View>
          <View style={styles.progressBarBackground}>
            <View style={[styles.progressBarFill, { width: `${progressPercentage}%` }]} />
          </View>
        </View>

        {/* Perguntas */}
        <View style={styles.questionsAccordion}>
          {perguntas.length > 0 ? ( // Verifica se há perguntas antes de mapear
            perguntas.map((pergunta, index) => (
              <View key={pergunta.id} style={styles.perguntaCard}>
                <View style={styles.cardHeader}>
                  <Text style={styles.perguntaNumber}>Pergunta #{index + 1}</Text>
                  <Text style={styles.badge}>{pergunta.tipo_resposta_display || pergunta.tipo_resposta}</Text>
                </View>
                <View style={styles.cardBody}>
                  <Text style={styles.perguntaText}>{pergunta.texto}</Text>
                  
                  {pergunta.tipo_resposta === 'SN' && (
                    <View style={styles.respostaButtonGroup}>
                      <TouchableOpacity
                        style={[styles.respostaButton, respostas[pergunta.id]?.valor === 'S' && styles.respostaButtonActiveSuccess]}
                        onPress={() => handleRespostaChange(pergunta.id, 'SN', 'S')}
                      >
                        <Text style={styles.respostaButtonText}>Sim</Text>
                      </TouchableOpacity>
                      <TouchableOpacity
                        style={[styles.respostaButton, respostas[pergunta.id]?.valor === 'N' && styles.respostaButtonActiveDanger]}
                        onPress={() => handleRespostaChange(pergunta.id, 'SN', 'N')}
                      >
                        <Text style={styles.respostaButtonText}>Não</Text>
                      </TouchableOpacity>
                    </View>
                  )}

                  {pergunta.tipo_resposta === 'NU' && (
                    <TextInput
                      style={styles.textInput}
                      keyboardType="numeric"
                      placeholder="Digite um número"
                      value={respostas[pergunta.id]?.valor || ''}
                      onChangeText={(text) => handleRespostaChange(pergunta.id, 'NU', text)}
                    />
                  )}

                  {pergunta.tipo_resposta === 'TX' && (
                    <TextInput
                      style={styles.textInputMultiline}
                      multiline
                      numberOfLines={4}
                      placeholder="Digite sua resposta"
                      value={respostas[pergunta.id]?.valor || ''}
                      onChangeText={(text) => handleRespostaChange(pergunta.id, 'TX', text)}
                    />
                  )}
                </View>
              </View>
            ))
          ) : (
            <View style={styles.emptyQuestionsContainer}>
              <Text style={styles.emptyQuestionsText}>Nenhuma pergunta encontrada para este questionário.</Text>
              <Text style={styles.emptyQuestionsSmallText}>Verifique sua conexão ou contate o administrador.</Text>
            </View>
          )}
        </View>

        {/* Botões de Ação */}
        <View style={styles.actionButtonsContainer}>
          <Button title="Enviar Respostas" onPress={handleSubmit} color="#007bff" />
        </View>

        {/* Botões de Navegação Adicionais */}
        <View style={styles.additionalButtonsContainer}>
          <TouchableOpacity 
            style={styles.additionalButton} 
            onPress={() => navigation.navigate('VisualizarQuestionario', { questionarioId: questionario.id, escolaId: escola.id, userData: userData })}
          >
            <Text style={styles.additionalButtonText}>Visualizar Relatório deste Questionário</Text>
          </TouchableOpacity>
          <TouchableOpacity 
            style={styles.additionalButton} 
            onPress={() => navigation.navigate('RelatarProblemas', { escolaId: escola.id, userData: userData })}
          >
            <Text style={styles.additionalButtonText}>Relatar Problemas para esta Escola</Text>
          </TouchableOpacity>
        </View>

      </ScrollView>
    </View>
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
  header: {
    marginBottom: 20,
    paddingBottom: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  headerInfo: {
    marginBottom: 10,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#0d6efd',
    marginBottom: 5,
  },
  headerSubtitle: {
    fontSize: 18,
    color: '#6c757d',
    marginBottom: 5,
  },
  headerDate: {
    fontSize: 14,
    color: '#6c757d',
  },
  questionarioTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  backButton: {
    backgroundColor: '#6c757d',
    paddingVertical: 8,
    paddingHorizontal: 15,
    borderRadius: 8,
    alignSelf: 'flex-start',
    marginTop: 10,
  },
  backButtonText: {
    color: 'white',
    fontWeight: 'bold',
  },
  progressContainer: {
    marginBottom: 20,
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  progressTextContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  progressBarBackground: {
    height: 10,
    backgroundColor: '#e9ecef',
    borderRadius: 10,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: '#0d6efd',
    borderRadius: 10,
  },
  questionsAccordion: {
    marginBottom: 20,
  },
  perguntaCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    marginBottom: 10,
    borderLeftWidth: 4,
    borderLeftColor: '#0d6efd',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
    padding: 15,
    borderTopLeftRadius: 8,
    borderTopRightRadius: 8,
  },
  perguntaNumber: {
    fontWeight: 'bold',
    color: '#333',
    fontSize: 16,
  },
  badge: {
    backgroundColor: '#6c757d',
    color: 'white',
    paddingVertical: 5,
    paddingHorizontal: 10,
    borderRadius: 5,
    fontSize: 12,
    fontWeight: 'bold',
  },
  cardBody: {
    padding: 15,
  },
  perguntaText: {
    fontSize: 16,
    marginBottom: 15,
    color: '#333',
  },
  respostaButtonGroup: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    borderRadius: 8,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#0d6efd',
  },
  respostaButton: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'white',
  },
  respostaButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#0d6efd',
  },
  respostaButtonActiveSuccess: {
    backgroundColor: '#28a745', // green
  },
  respostaButtonActiveDanger: {
    backgroundColor: '#dc3545', // red
  },
  textInput: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 10,
    fontSize: 16,
    backgroundColor: 'white',
  },
  textInputMultiline: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 10,
    fontSize: 16,
    backgroundColor: 'white',
    minHeight: 100,
    textAlignVertical: 'top', // Para Android, alinha o texto no topo em multiline
  },
  actionButtonsContainer: {
    marginTop: 20,
    marginBottom: 20,
  },
  additionalButtonsContainer: {
    marginTop: 10,
    marginBottom: 20,
    alignItems: 'center',
  },
  additionalButton: {
    backgroundColor: '#6c757d',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    marginBottom: 10,
    width: '100%',
    alignItems: 'center',
  },
  additionalButtonText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 16,
  },
  emptyQuestionsContainer: { // Novo estilo para quando não há perguntas
    alignItems: 'center',
    paddingVertical: 50,
  },
  emptyQuestionsText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#6c757d',
    marginBottom: 5,
    textAlign: 'center',
  },
  emptyQuestionsSmallText: {
    fontSize: 14,
    color: '#6c757d',
    textAlign: 'center',
  },
});

export default ResponderQuestionarioScreen;
