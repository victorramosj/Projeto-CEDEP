// GerarRelatorioPdfScreen.js
import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
  ScrollView,
  Alert,
  Share, // Para compartilhar o PDF (opcional)
  Platform, // Para verificar a plataforma
} from 'react-native';
import { useRoute, useNavigation } from '@react-navigation/native';
import axios from 'axios';
import RNHTMLtoPDF from 'react-native-html-to-pdf'; // Biblioteca para gerar PDF
import * as FileSystem from 'expo-file-system'; // Ou 'react-native-fs' para CLI puro
import * as Sharing from 'expo-sharing'; // Para Expo: Compartilhar arquivos

// URL base da sua API Django
const API_BASE_URL = 'http://10.0.2.2:8000'; // Para emulador Android

const GerarRelatorioPdfScreen = () => {
  const route = useRoute();
  const navigation = useNavigation();
  const { escolaId, userData } = route.params;

  const [loading, setLoading] = useState(true);
  const [relatorioData, setRelatorioData] = useState(null);
  const [pdfPath, setPdfPath] = useState(null);

  const fetchRelatorioData = useCallback(async () => {
    setLoading(true);
    try {
      const token = userData?.token;
      if (!token) {
        Alert.alert('Erro de Autenticação', 'Token não encontrado. Faça login novamente.');
        navigation.replace('Login');
        return;
      }

      const response = await axios.get(`${API_BASE_URL}/api/relatorio-diario/${escolaId}/`, {
        headers: { 'Authorization': `Token ${token}` },
      });
      setRelatorioData(response.data);
    } catch (error) {
      console.error('Erro ao buscar dados do relatório:', error.response?.data || error.message);
      Alert.alert('Erro', 'Não foi possível carregar os dados do relatório.');
      navigation.goBack(); // Volta se falhar
    } finally {
      setLoading(false);
    }
  }, [escolaId, userData, navigation]);

  useEffect(() => {
    fetchRelatorioData();
  }, [fetchRelatorioData]);

  const generateHtml = (data) => {
    if (!data) return '';

    // Adapte este HTML para refletir o seu template Django, mas como uma string JS
    // Você pode usar template literals (` `) para injetar variáveis.
    // Lembre-se: Imagens e estilos CSS precisam ser carregados de URLs acessíveis
    // ou incorporados (base64) para funcionarem no PDF.
    // Para imagens de comprovantes: certifique-se que as URLs são absolutas e acessíveis publicamente.

    let questionariosHtml = '';
    if (data.questionarios && data.questionarios.length > 0) {
        data.questionarios.forEach(q => {
            let monitoramentosHtml = '';
            q.monitoramentos.forEach(m => {
                let respostasHtml = '';
                m.respostas.forEach(r => {
                    let respostaValor = '-';
                    if (r.pergunta.tipo_resposta === 'SN') {
                        respostaValor = r.resposta_sn_display || '-';
                    } else if (r.pergunta.tipo_resposta === 'NU') {
                        respostaValor = r.resposta_num !== null ? r.resposta_num.toString() : '-';
                    } else {
                        respostaValor = r.resposta_texto || '-';
                    }
                    respostasHtml += `
                        <div class="resposta-item">
                            <div class="pergunta-texto">${r.pergunta.ordem}. ${r.pergunta.texto}</div>
                            <div class="resposta-valor">${respostaValor}</div>
                        </div>
                    `;
                });

                let fotoHtml = '';
                if (m.foto_comprovante_url) { // Use foto_comprovante_url do serializer
                    fotoHtml = `
                        <div class="foto-container">
                            <span class="foto-label">Foto Comprobatória:</span>
                            <img src="${m.foto_comprovante_url}" class="foto-comprovante">
                        </div>
                    `;
                }
                
                monitoramentosHtml += `
                    <div class="monitoramento-card">
                        <div class="monitoramento-info">
                            <div class="info-grid">
                                <div class="info-label">Responsável:</div>
                                <div>${m.respondido_por.greuser?.nome_completo || m.respondido_por.username || 'Não identificado'}</div>
                                <div class="info-label">Data/Hora:</div>
                                <div>${new Date(m.criado_em).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })}</div>
                                <div class="info-label">Escola:</div>
                                <div>${m.escola.nome}</div>
                            </div>
                        </div>
                        <div class="respostas-container">
                            ${respostasHtml}
                        </div>
                        ${fotoHtml}
                    </div>
                `;
            });
            questionariosHtml += `
                <div class="questionario-card">
                    <div class="questionario-header">
                        ${q.titulo} - Setor: ${q.setor.nome}
                    </div>
                    ${monitoramentosHtml}
                </div>
            `;
        });
    } else {
        questionariosHtml = `<div class="info-card"><p style="text-align: center; padding: 3mm; color: #6c757d;">Nenhum monitoramento encontrado para este relatório.</p></div>`;
    }

    // Adicione a seção de Problemas e Lacunas
    let problemasHtml = '';
    if (data.problemas_hoje && data.problemas_hoje.length > 0) {
        problemasHtml = `
            <div class="section">
                <div class="section-header">Problemas Relatados Hoje</div>
                ${data.problemas_hoje.map(p => `
                    <div class="info-card">
                        <div class="info-grid">
                            <div class="info-label">Descrição:</div>
                            <div>${p.descricao}</div>
                            <div class="info-label">Setor:</div>
                            <div>${p.setor_detalhes?.nome || 'N/A'}</div>
                            <div class="info-label">Status:</div>
                            <div>${p.status_display}</div>
                            <div class="info-label">Relatado por:</div>
                            <div>${p.usuario?.greuser?.nome_completo || p.usuario?.user?.username || 'N/A'}</div>
                            ${p.anexo_url ? `<div class="info-label">Anexo:</div><div><img src="${p.anexo_url}" style="max-width: 80mm; max-height: 50mm;"></div>` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    let lacunasHtml = '';
    if (data.lacunas_hoje && data.lacunas_hoje.length > 0) {
        lacunasHtml = `
            <div class="section">
                <div class="section-header">Lacunas Relatadas Hoje</div>
                ${data.lacunas_hoje.map(l => `
                    <div class="info-card">
                        <div class="info-grid">
                            <div class="info-label">Disciplina:</div>
                            <div>${l.disciplina}</div>
                            <div class="info-label">Carga Horária:</div>
                            <div>${l.carga_horaria} horas</div>
                            <div class="info-label">Status:</div>
                            <div>${l.status_display}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }


    const cssStyles = `
        /* Inclua aqui todo o CSS do seu template HTML relatorio.html */
        /* Garanta que as imagens em 'src' sejam URLs absolutas e acessíveis */
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.4;
            color: #333;
            background-color: #fff;
            margin: 0;
            padding: 5mm;
            font-size: 10pt;
        }

        .header {
            text-align: center;
            margin-bottom: 5mm;
            padding-bottom: 3mm;
            border-bottom: 1.5pt solid #2c3e50;
        }

        .header h1 {
            margin: 0 0 1mm 0;
            color: #2c3e50;
            font-size: 14pt;
            font-weight: 700;
        }

        .header .subtitle {
            font-size: 9pt;
            color: #7f8c8d;
            margin-top: 1mm;
        }

        .header .date {
            font-size: 8pt;
            color: #3498db;
            font-weight: 500;
        }

        .section {
            margin-bottom: 5mm;
            /* page-break-inside: avoid; remova isso para HTML pois não afeta na geração de PDF de html-to-pdf */
        }

        .section-header {
            background-color: #2c3e50;
            color: white;
            padding: 2mm 3mm;
            margin-bottom: 3mm;
            font-size: 10pt;
            font-weight: 600;
        }

        .info-card {
            background-color: #f8f9fa;
            border: 0.5pt solid #dee2e6;
            border-radius: 2pt;
            padding: 3mm;
            margin-bottom: 3mm;
        }

        .info-grid {
            display: grid;
            grid-template-columns: max-content auto;
            gap: 2mm 3mm;
            font-size: 9pt;
        }

        .info-label {
            font-weight: bold;
            color: #2c3e50;
            text-align: right;
        }

        .questionario-card {
            border: 0.5pt solid #dee2e6;
            border-radius: 2pt;
            margin-bottom: 4mm;
            overflow: hidden;
            /* page-break-inside: avoid; */
        }

        .questionario-header {
            background-color: #3498db;
            color: white;
            padding: 2mm 3mm;
            font-size: 10pt;
            font-weight: 600;
        }

        .monitoramento-card {
            border-bottom: 0.5pt solid #eee;
            padding: 3mm;
        }

        .monitoramento-info {
            margin-bottom: 3mm;
            padding-bottom: 2mm;
            border-bottom: 0.5pt dashed #eee;
        }

        .resposta-item {
            margin-bottom: 2mm;
            padding-bottom: 2mm;
        }

        .pergunta-texto {
            font-weight: bold;
            margin-bottom: 1mm;
            color: #2c3e50;
            font-size: 9pt;
        }

        .resposta-valor {
            padding: 2mm 3mm;
            background-color: #f8f9fa;
            border-left: 1.5pt solid #3498db;
            border-radius: 0 1pt 1pt 0;
            font-size: 9pt;
        }

        .foto-container {
            margin-top: 3mm;
            text-align: center;
        }

        .foto-label {
            font-weight: bold;
            display: block;
            margin-bottom: 1mm;
            color: #2c3e50;
            font-size: 9pt;
        }

        .foto-comprovante {
            max-width: 120mm;
            max-height: 70mm;
            border: 0.5pt solid #ddd;
        }

        .summary-card {
            background-color: #e3f2fd;
            border: 0.5pt solid #bbdefb;
            border-radius: 2pt;
            padding: 3mm;
            margin-bottom: 3mm;
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 2mm;
        }

        .summary-item {
            text-align: center;
            padding: 2mm;
            background-color: white;
            border-radius: 2pt;
        }

        .summary-value {
            font-size: 14pt;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 1mm;
        }

        .summary-label {
            font-size: 8pt;
            color: #7f8c8d;
        }

        .signature-area {
            margin-top: 10mm;
            padding-top: 2mm;
            border-top: 0.5pt solid #ddd;
            text-align: center;
        }

        .signature-line {
            display: inline-block;
            width: 60mm;
            border-bottom: 0.5pt solid #333;
            margin-bottom: 1mm;
        }

        .signature-label {
            font-size: 8pt;
            color: #7f8c8d;
        }

        .entities-list {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 2mm;
            margin-top: 2mm;
        }

        .entity-card {
            background-color: #fff;
            border: 0.5pt solid #dee2e6;
            border-radius: 2pt;
            padding: 2mm;
            font-size: 8pt;
        }

        .entity-name {
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 1mm;
        }
    `;

    return `
      <!DOCTYPE html>
      <html>
      <head>
          <meta charset="UTF-8">
          <style>${cssStyles}</style>
      </head>
      <body>
          <div class="header">
              <h1>Relatório de Monitoramento</h1>
              <div class="subtitle">Escola: ${data.escola.nome} | Data: ${data.data}</div>
              <div class="date">Gerado por: ${userData.username || 'Usuário'}</div>
          </div>

          <div class="section">
              <div class="section-header">Resumo Geral</div>
              <div class="summary-card">
                  <div class="summary-grid">
                      <div class="summary-item">
                          <div class="summary-value">${data.total_questionarios}</div>
                          <div class="summary-label">Questionários</div>
                      </div>
                      <div class="summary-item">
                          <div class="summary-value">${data.total_monitoramentos}</div>
                          <div class="summary-label">Monitoramentos</div>
                      </div>
                      <div class="summary-item">
                          <div class="summary-value">${data.setores_envolvidos}</div>
                          <div class="summary-label">Setores</div>
                      </div>
                      <div class="summary-item">
                          <div class="summary-value">${data.usuarios_envolvidos.length}</div>
                          <div class="summary-label">Responsáveis</div>
                      </div>
                  </div>
                  ${data.usuarios_envolvidos.length > 0 ? `
                  <div class="section-header" style="margin-top: 4mm;">Responsáveis Envolvidos</div>
                  <div class="info-card">
                    <div class="entities-list">
                      ${data.usuarios_envolvidos.map(user => `<div class="entity-card"><div class="entity-name">${user}</div></div>`).join('')}
                    </div>
                  </div>
                  ` : ''}
              </div>
          </div>

          ${problemasHtml}
          ${lacunasHtml}

          <div class="section">
              <div class="section-header">Detalhamento por Monitoramento</div>
              ${questionariosHtml}
          </div>

          <div class="signature-area">
              <div class="signature-line"></div>
              <div class="signature-label">Assinatura do Responsável (Monitor)</div>
              <p style="font-size: 8pt; color: #7f8c8d;">Gerado eletronicamente em ${new Date().toLocaleString('pt-BR')}</p>
          </div>
      </body>
      </html>
    `;
  };

  const generateAndSharePdf = async () => {
    if (!relatorioData) {
      Alert.alert('Erro', 'Dados do relatório não carregados.');
      return;
    }

    setLoading(true);
    try {
      const htmlContent = generateHtml(relatorioData);
      const options = {
        html: htmlContent,
        fileName: `Relatorio_Escola_${relatorioData.escola.nome.replace(/ /g, '_')}_${relatorioData.data}.pdf`,
        directory: Platform.OS === 'android' ? 'Download' : 'Documents', // Salva em Downloads no Android, Documentos no iOS
        base64: false, // Não precisa do base64 se for apenas para salvar/compartilhar
        height: 842, // Altura de uma página A4 em pontos (aprox)
        width: 595,  // Largura de uma página A4 em pontos (aprox)
      };

      const pdf = await RNHTMLtoPDF.convert(options);
      setPdfPath(pdf.filePath);

      Alert.alert(
        'PDF Gerado!',
        `O relatório foi salvo em: ${pdf.filePath}`,
        [
          { text: 'OK', style: 'cancel' },
          { text: 'Compartilhar', onPress: () => sharePdf(pdf.filePath) },
        ],
        { cancelable: true }
      );
    } catch (error) {
      console.error('Erro ao gerar PDF:', error);
      Alert.alert('Erro', 'Não foi possível gerar o PDF do relatório.');
    } finally {
      setLoading(false);
    }
  };

  const sharePdf = async (filePath) => {
    try {
      if (Platform.OS === 'android') {
        // No Android, `react-native-html-to-pdf` já salva no diretório de downloads.
        // O `Sharing` do Expo pode precisar de permissões adicionais ou de uma URI de conteúdo.
        // Para CLI puro no Android, você pode precisar usar `react-native-share` ou similar.
        // Para este exemplo, vamos assumir que o Expo Sharing pode lidar com `file://` URIs do FS.
        await Sharing.shareAsync(filePath);
      } else { // iOS
        // No iOS, `react-native-html-to-pdf` salva em um local temporário.
        // `Sharing.shareAsync` é a maneira correta de abrir a folha de compartilhamento.
        await Sharing.shareAsync(filePath);
      }
    } catch (error) {
      console.error('Erro ao compartilhar PDF:', error);
      Alert.alert('Erro', 'Não foi possível compartilhar o PDF.');
    }
  };

  if (loading && !relatorioData) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#0000ff" />
        <Text style={styles.loadingText}>Carregando dados do relatório...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.contentContainer}>
        <Text style={styles.title}>Relatório Diário da Escola</Text>
        {relatorioData ? (
          <>
            <Text style={styles.subtitle}>Escola: {relatorioData.escola.nome}</Text>
            <Text style={styles.subtitle}>Data: {relatorioData.data}</Text>
            <Text style={styles.subtitle}>Gerado por: {userData.username}</Text>

            <View style={styles.sectionSummary}>
              <Text style={styles.sectionTitle}>Resumo</Text>
              <View style={styles.summaryGrid}>
                <View style={styles.summaryItem}>
                  <Text style={styles.summaryValue}>{relatorioData.total_questionarios}</Text>
                  <Text style={styles.summaryLabel}>Questionários</Text>
                </View>
                <View style={styles.summaryItem}>
                  <Text style={styles.summaryValue}>{relatorioData.total_monitoramentos}</Text>
                  <Text style={styles.summaryLabel}>Monitoramentos</Text>
                </View>
                <View style={styles.summaryItem}>
                  <Text style={styles.summaryValue}>{relatorioData.setores_envolvidos}</Text>
                  <Text style={styles.summaryLabel}>Setores</Text>
                </View>
                <View style={styles.summaryItem}>
                  <Text style={styles.summaryValue}>{relatorioData.usuarios_envolvidos.length}</Text>
                  <Text style={styles.summaryLabel}>Responsáveis</Text>
                </View>
              </View>
              {relatorioData.usuarios_envolvidos.length > 0 && (
                <View style={styles.responsibleList}>
                  <Text style={styles.responsibleListTitle}>Responsáveis Envolvidos:</Text>
                  {relatorioData.usuarios_envolvidos.map((user, index) => (
                    <Text key={index} style={styles.responsibleItem}>- {user}</Text>
                  ))}
                </View>
              )}
            </View>

            {/* Renderização de Problemas e Lacunas se existirem */}
            {relatorioData.problemas_hoje && relatorioData.problemas_hoje.length > 0 && (
                <View style={styles.sectionDetail}>
                    <Text style={styles.sectionTitle}>Problemas Relatados Hoje</Text>
                    {relatorioData.problemas_hoje.map(p => (
                        <View key={p.id} style={styles.reportItemCard}>
                            <Text style={styles.reportItemTitle}>Problema: {p.descricao.substring(0, 50)}...</Text>
                            <Text style={styles.reportItemDetail}>Setor: {p.setor_detalhes?.nome || 'N/A'}</Text>
                            <Text style={styles.reportItemDetail}>Status: {p.status_display}</Text>
                            <Text style={styles.reportItemDetail}>Relatado por: {p.usuario?.greuser?.nome_completo || p.usuario?.user?.username || 'N/A'}</Text>
                            {p.anexo_url && <Text style={styles.reportItemDetail}>Anexo disponível no PDF</Text>}
                        </View>
                    ))}
                </View>
            )}

            {relatorioData.lacunas_hoje && relatorioData.lacunas_hoje.length > 0 && (
                <View style={styles.sectionDetail}>
                    <Text style={styles.sectionTitle}>Lacunas Relatadas Hoje</Text>
                    {relatorioData.lacunas_hoje.map(l => (
                        <View key={l.id} style={styles.reportItemCard}>
                            <Text style={styles.reportItemTitle}>Disciplina: {l.disciplina}</Text>
                            <Text style={styles.reportItemDetail}>Carga Horária: {l.carga_horaria}h</Text>
                            <Text style={styles.reportItemDetail}>Status: {l.status_display}</Text>
                        </View>
                    ))}
                </View>
            )}

            {/* Parte de detalhamento dos questionários no app (simplificado) */}
            {relatorioData.questionarios && relatorioData.questionarios.length > 0 ? (
                <View style={styles.sectionDetail}>
                    <Text style={styles.sectionTitle}>Detalhes dos Monitoramentos</Text>
                    {relatorioData.questionarios.map(q => (
                        <View key={q.id} style={styles.questionarioAppCard}>
                            <Text style={styles.questionarioAppTitle}>{q.titulo} - {q.setor.nome}</Text>
                            {q.monitoramentos.map(m => (
                                <View key={m.id} style={styles.monitoramentoAppCard}>
                                    <Text style={styles.monitoramentoAppText}>Responsável: {m.respondido_por.greuser?.nome_completo || m.respondido_por.username}</Text>
                                    <Text style={styles.monitoramentoAppText}>Hora: {new Date(m.criado_em).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}</Text>
                                    <Text style={styles.monitoramentoAppSubTitle}>Respostas:</Text>
                                    {m.respostas.map(r => (
                                        <Text key={r.id} style={styles.respostaAppText}>
                                            {r.pergunta.ordem}. {r.pergunta.texto}: {r.resposta_sn_display || r.resposta_num || r.resposta_texto || '-'}
                                        </Text>
                                    ))}
                                    {m.foto_comprovante_url && (
                                      <Text style={styles.monitoramentoAppText}>Foto comprovante: [Disponível no PDF]</Text>
                                    )}
                                </View>
                            ))}
                        </View>
                    ))}
                </View>
            ) : (
              <Text style={styles.noDataText}>Nenhum monitoramento registrado hoje.</Text>
            )}
          </>
        ) : (
          <Text style={styles.noDataText}>Nenhum dado de relatório para exibir.</Text>
        )}
      </ScrollView>

      <TouchableOpacity
        style={styles.generatePdfButton}
        onPress={generateAndSharePdf}
        disabled={loading || !relatorioData}
      >
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.generatePdfButtonText}>Gerar e Salvar PDF</Text>
        )}
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  contentContainer: {
    padding: 20,
    paddingBottom: 100, // Espaço extra para o botão flutuante
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
  title: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#26326D',
    marginBottom: 5,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#546E7A',
    marginBottom: 3,
    textAlign: 'center',
  },
  noDataText: {
    textAlign: 'center',
    marginTop: 50,
    fontSize: 16,
    color: '#7f8c8d',
  },
  sectionSummary: {
    backgroundColor: '#e3f2fd',
    borderRadius: 8,
    padding: 15,
    marginTop: 20,
    borderColor: '#bbdefb',
    borderWidth: 1,
  },
  sectionDetail: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 15,
    marginTop: 20,
    borderColor: '#eee',
    borderWidth: 1,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#ccc',
    paddingBottom: 5,
  },
  summaryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-around',
    marginBottom: 10,
  },
  summaryItem: {
    alignItems: 'center',
    width: '45%', // Duas colunas
    padding: 10,
    backgroundColor: '#fff',
    borderRadius: 5,
    margin: 5,
    elevation: 1,
  },
  summaryValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2c3e50',
  },
  summaryLabel: {
    fontSize: 12,
    color: '#7f8c8d',
    textAlign: 'center',
  },
  responsibleList: {
    marginTop: 15,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: '#dbe9f5',
  },
  responsibleListTitle: {
    fontSize: 15,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 8,
  },
  responsibleItem: {
    fontSize: 14,
    color: '#546E7A',
    marginLeft: 10,
    marginBottom: 3,
  },
  questionarioAppCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 10,
    marginBottom: 10,
    borderColor: '#ddd',
    borderWidth: 1,
  },
  questionarioAppTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#3498db',
    marginBottom: 8,
  },
  monitoramentoAppCard: {
    backgroundColor: '#fff',
    padding: 10,
    borderRadius: 6,
    marginBottom: 8,
    borderLeftWidth: 3,
    borderLeftColor: '#28a745',
  },
  monitoramentoAppText: {
    fontSize: 13,
    color: '#546E7A',
    marginBottom: 3,
  },
  monitoramentoAppSubTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginTop: 5,
    marginBottom: 5,
  },
  respostaAppText: {
    fontSize: 13,
    color: '#333',
    marginLeft: 5,
    marginBottom: 2,
  },
  reportItemCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 10,
    marginBottom: 10,
    borderColor: '#f0ad4e', // Cor para problemas/lacunas
    borderWidth: 1,
  },
  reportItemTitle: {
    fontSize: 15,
    fontWeight: 'bold',
    color: '#d9534f', // Cor de problema
    marginBottom: 5,
  },
  reportItemDetail: {
    fontSize: 13,
    color: '#546E7A',
    marginBottom: 3,
  },
  generatePdfButton: {
    backgroundColor: '#007bff',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    position: 'absolute', // Faz o botão flutuar
    bottom: 20,
    left: 20,
    right: 20,
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  generatePdfButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
});

export default GerarRelatorioPdfScreen;