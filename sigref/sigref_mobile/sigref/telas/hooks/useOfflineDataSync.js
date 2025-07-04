import { useState, useEffect, useCallback } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import axios from 'axios';
import { Alert } from 'react-native'; // Para alertas simples

const OFFLINE_MASTER_DATA_KEY = '@offline_master_data';
const LAST_SYNC_TIMESTAMP_KEY = '@last_master_data_sync';
const SYNC_INTERVAL_MS = 24 * 60 * 60 * 1000; // 24 horas em milissegundos para forçar uma nova sincronização

//const API_BASE_URL = 'http://127.0.0.1:8000'; // para pc
const API_BASE_URL = 'http://10.0.2.2:8000'; //para emulador android
//const API_BASE_URL = 'https://grefloresta.com.br'; // URL do servidor remoto

const useOfflineDataSync = (userData) => { // Removida a prop `initialLoad` daqui
  const [offlineData, setOfflineData] = useState({
    escolas: [],
    questionarios: [],
    perguntas: [],
    setores: []
  });
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncError, setSyncError] = useState(null);
  const [lastSync, setLastSync] = useState(null); // Timestamp da última sincronização
  const [isConnected, setIsConnected] = useState(true);
  const [hasInitialSyncAttempted, setHasInitialSyncAttempted] = useState(false); // NOVO ESTADO

  // Listener de conexão
  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener(state => {
      setIsConnected(state.isConnected);
      console.log('useOfflineDataSync: Status da conexão:', state.isConnected ? 'Online' : 'Offline');
    });
    return () => unsubscribe();
  }, []);

  // Função para carregar dados do cache local
  const loadCachedData = useCallback(async () => {
    try {
      const cachedDataString = await AsyncStorage.getItem(OFFLINE_MASTER_DATA_KEY);
      if (cachedDataString) {
        const parsedData = JSON.parse(cachedDataString);
        setOfflineData(parsedData);
        console.log('useOfflineDataSync: Dados mestres carregados do cache.');
      } else {
        console.log('useOfflineDataSync: Nenhum dado mestre encontrado no cache.');
      }
      const lastSyncString = await AsyncStorage.getItem(LAST_SYNC_TIMESTAMP_KEY);
      if (lastSyncString) {
        setLastSync(parseInt(lastSyncString, 10));
      }
    } catch (e) {
      console.error('useOfflineDataSync: Erro ao carregar dados do cache:', e);
      setSyncError('Erro ao carregar dados locais.');
    }
  }, []);

  // Função para buscar e salvar todos os dados da API
  const fetchAndSaveAllData = useCallback(async (token) => {
    if (!token) {
      console.warn('useOfflineDataSync: Token de autenticação ausente para sincronização.');
      setSyncError('Token de autenticação ausente para sincronização.');
      return false;
    }

    setIsSyncing(true);
    setSyncError(null);
    console.log('useOfflineDataSync: Tentando buscar todos os dados mestres da API...');

    try {
      const response = await axios.get(`${API_BASE_URL}/monitoramento/api/all-offline-data/`, {
        headers: {
          'Authorization': `Token ${token}`,
        },
        timeout: 30000, 
      });

      const newMasterData = response.data;
      setOfflineData(newMasterData);
      await AsyncStorage.setItem(OFFLINE_MASTER_DATA_KEY, JSON.stringify(newMasterData));
      const now = Date.now();
      await AsyncStorage.setItem(LAST_SYNC_TIMESTAMP_KEY, now.toString());
      setLastSync(now); // Atualiza o estado lastSync
      setHasInitialSyncAttempted(true); // Marca que a sincronização inicial foi tentada
      console.log('useOfflineDataSync: Todos os dados mestres sincronizados com sucesso.');
      Alert.alert('Sincronização', 'Dados atualizados com o servidor.');
      return true;

    } catch (error) {
      console.error('useOfflineDataSync: Erro ao sincronizar dados mestres:', error.response?.data || error.message);
      setSyncError(error.response?.data?.detail || 'Erro ao sincronizar dados mestres. Verifique sua conexão.');
      setHasInitialSyncAttempted(true); // Marca que a sincronização inicial foi tentada, mesmo com erro
      return false;
    } finally {
      setIsSyncing(false);
    }
  }, []);

  // Efeito principal para gerenciar o carregamento e sincronização
  useEffect(() => {
    console.log('useOfflineDataSync: useEffect principal acionado.');
    loadCachedData(); // Sempre carrega o cache na montagem do hook

    const syncOnConnect = async () => {
        // Apenas procede se conectado, userData disponível e não estiver já sincronizando
        if (isConnected && userData?.token && !isSyncing) {
            const currentLastSync = lastSync; // Usa o estado atual do lastSync
            
            // Lógica para decidir se deve sincronizar:
            // 1. Nunca sincronizou antes E a tentativa inicial ainda não ocorreu.
            // 2. Ou, já passou do intervalo de sincronização (24h).
            const shouldSync = (!currentLastSync && !hasInitialSyncAttempted) || 
                             (currentLastSync && (Date.now() - currentLastSync > SYNC_INTERVAL_MS));
            
            console.log(`useOfflineDataSync: syncOnConnect check -> shouldSync: ${shouldSync}, isConnected: ${isConnected}, isSyncing: ${isSyncing}, hasInitialSyncAttempted: ${hasInitialSyncAttempted}`);
            
            if (shouldSync) {
                await fetchAndSaveAllData(userData.token);
            }
        }
    };

    // Pequeno atraso para garantir que a conexão esteja estável no início
    const timer = setTimeout(syncOnConnect, 1000); 
    
    return () => clearTimeout(timer); // Limpa o timer ao desmontar ou re-executar o efeito

  }, [isConnected, userData?.token, fetchAndSaveAllData, loadCachedData, hasInitialSyncAttempted, isSyncing, lastSync]); // lastSync é uma dependência para que a lógica de "shouldSync" seja reavaliada quando ele muda.

  // Retorna os dados offline e o estado de sincronização
  return { offlineData, isSyncing, syncError, triggerMasterSync: fetchAndSaveAllData, isConnected };
};

export default useOfflineDataSync;
