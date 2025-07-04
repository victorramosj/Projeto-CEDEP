// RelatarLacunaScreen.js
import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  ScrollView,
  Alert,
  KeyboardAvoidingView, // Para evitar que o teclado cubra campos
  Platform,
} from 'react-native';
import { useRoute, useNavigation } from '@react-navigation/native';
import axios from 'axios';

// URL base da sua API Django (ajuste conforme necessário)
const API_BASE_URL = 'http://10.0.2.2:8000'; // Para emulador Android

const RelatarLacunaScreen = () => {
  const route = useRoute();
  const navigation = useNavigation();
  const { escolaId, userData } = route.params;

  const [disciplina, setDisciplina] = useState('');
  const [cargaHoraria, setCargaHoraria] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!disciplina.trim() || !cargaHoraria.trim()) {
      Alert.alert('Erro', 'Por favor, preencha todos os campos.');
      return;
    }

    const cargaHorariaNum = parseInt(cargaHoraria, 10);
    if (isNaN(cargaHorariaNum) || cargaHorariaNum <= 0) {
      Alert.alert('Erro', 'A carga horária deve ser um número positivo.');
      return;
    }

    setLoading(true);

    try {
      const token = userData?.token;
      if (!token) {
        Alert.alert('Erro de Autenticação', 'Token de autenticação não encontrado. Faça login novamente.');
        navigation.replace('Login');
        return;
      }

      const dataLacuna = {
        escola: escolaId,
        disciplina: disciplina,
        carga_horaria: cargaHorariaNum,
        // O status será o padrão do modelo Django ('P' - Pendente)
      };

      const response = await axios.post(`${API_BASE_URL}/api/lacunas/`, dataLacuna, {
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.status === 201) { // 201 Created é o status de sucesso para POST
        Alert.alert('Sucesso', 'Lacuna relatada com sucesso!');
        navigation.goBack(); // Volta para a tela anterior (SchoolDashboardScreen)
      } else {
        Alert.alert('Erro', `Falha ao relatar lacuna: ${response.data.detail || JSON.stringify(response.data)}`);
      }
    } catch (error) {
      console.error('Erro ao enviar lacuna:', error.response?.data || error.message);
      Alert.alert('Erro', 'Não foi possível relatar a lacuna. Verifique sua conexão ou tente novamente. Detalhes: ' + (error.response?.data ? JSON.stringify(error.response.data) : error.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.contentContainer}>
        <Text style={styles.title}>Relatar Nova Lacuna</Text>

        <Text style={styles.label}>Escola:</Text>
        <TextInput
          style={styles.readOnlyInput}
          value={escolaId.toString()} // Exibe o ID da escola, é read-only
          editable={false}
        />

        <Text style={styles.label}>Disciplina:</Text>
        <TextInput
          style={styles.input}
          placeholder="Nome da disciplina (Ex: Matemática, Português)"
          value={disciplina}
          onChangeText={setDisciplina}
        />

        <Text style={styles.label}>Carga Horária (em horas-aula):</Text>
        <TextInput
          style={styles.input}
          placeholder="Ex: 80, 40"
          keyboardType="numeric"
          value={cargaHoraria}
          onChangeText={setCargaHoraria}
        />

        <TouchableOpacity
          style={styles.submitButton}
          onPress={handleSubmit}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.submitButtonText}>Enviar Lacuna</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.cancelButton}
          onPress={() => navigation.goBack()}
          disabled={loading}
        >
          <Text style={styles.cancelButtonText}>Cancelar</Text>
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  contentContainer: {
    padding: 20,
    paddingBottom: 40, // Adicione padding inferior para ScrollView
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#26326D',
    marginBottom: 20,
    textAlign: 'center',
  },
  label: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#546E7A',
    marginBottom: 8,
    marginTop: 15,
  },
  input: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 10,
  },
  readOnlyInput: {
    backgroundColor: '#e0e0e0',
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 10,
    color: '#666',
  },
  submitButton: {
    backgroundColor: '#28a745', // Verde para sucesso
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    marginTop: 20,
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  cancelButton: {
    backgroundColor: '#dc3545', // Vermelho para cancelar
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    marginTop: 10,
  },
  cancelButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
});

export default RelatarLacunaScreen;