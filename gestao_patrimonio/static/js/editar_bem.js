document.addEventListener('DOMContentLoaded', function() {
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    function setupModalForm(formId, url, selectId) {
        const form = document.getElementById(formId);
        if (!form) return;

        form.addEventListener('submit', function(e) {
            e.preventDefault();
            let formData = new FormData(form);
            let data = {};
            formData.forEach((value, key) => { data[key] = value });

            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify(data)
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => { throw err; });
                }
                return response.json();
            })
            .then(result => {
                if (result.success) {
                    alert('Criado com sucesso!');
                    if (selectId) {
                        const select = document.getElementById(selectId);
                        if (select) {
                            let option = new Option(result.nome, result.id);
                            select.add(option);
                        }
                    }
                    let modalElement = document.getElementById(formId.replace('Form', 'Modal'));
                    if (modalElement) {
                        let modalInstance = bootstrap.Modal.getInstance(modalElement) || new bootstrap.Modal(modalElement);
                        modalInstance.hide();
                    }
                    form.reset();
                } else {
                    let errorMessage = result.error || 'Erro ao criar.';
                    if (result.errors) {
                        errorMessage += "\n" + JSON.stringify(result.errors, null, 2);
                    }
                    alert(errorMessage);
                }
            })
            .catch(error => {
                console.error('Erro:', error);

                let errorMessage = 'Erro ao processar a solicitação.';

                if (typeof error === 'object' && error !== null) {
                    if (error.errors) {
                        errorMessage += '\n\nDetalhes:\n';
                        for (const [campo, mensagens] of Object.entries(error.errors)) {
                            errorMessage += `- ${campo}: ${mensagens.join(', ')}\n`;
                        }
                    } else if (error.detail) {
                        errorMessage += `\n\nDetalhe: ${error.detail}`;
                    }
                } else {
                    errorMessage += '\n\nErro inesperado.';
                }

                // Exibe o erro no alert
                alert(errorMessage);
            });
        });
    }

    setupModalForm('categoriaForm', '/api/criar_categoria/', 'categoria');
    setupModalForm('departamentoForm', '/api/criar_departamento/', 'departamento');
    setupModalForm('fornecedorForm', '/api/criar_fornecedor/', 'fornecedor');
    
});