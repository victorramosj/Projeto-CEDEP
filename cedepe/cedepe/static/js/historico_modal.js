function showHistorico(bemId) {
  const modalElement = document.getElementById('historicoModal');
  const modalTitle = document.getElementById('historicoModalLabel');
  const modalBody = document.getElementById('historicoModalBody');
  const modal = new bootstrap.Modal(modalElement);

  // Exibe indicador de carregamento
  modalBody.innerHTML = `
    <div class="text-center">
      <div class="spinner-border" role="status">
        <span class="visually-hidden">Carregando...</span>
      </div>
    </div>`;

  modal.show();

  // Requisição AJAX
  fetch(`/api/historico_item/${bemId}/`)
    .then(response => response.json())
    .then(data => {
      modalTitle.textContent = `Histórico do Bem: ${data.bem_nome}`;
      modalBody.innerHTML = data.html;
    })
    .catch(error => {
      modalBody.innerHTML = '<div class="alert alert-danger">Erro ao carregar histórico.</div>';
      console.error('Erro:', error);
    });
}