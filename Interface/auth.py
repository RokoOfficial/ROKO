
import hashlib
import secrets
import functools
from flask import session, request, jsonify, redirect, url_for
import logging

class AuthSystem:
    """Sistema de autenticação para MOMO."""
    
    def __init__(self, memory_system):
        self.memory = memory_system
    
    def hash_password(self, password: str) -> str:
        """Gera hash seguro da senha."""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{password_hash.hex()}"
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verifica se a senha está correta."""
        try:
            salt, hash_hex = password_hash.split(':')
            password_check = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return password_check.hex() == hash_hex
        except ValueError:
            return False
    
    def register_user(self, username: str, email: str, password: str) -> dict:
        """Registra novo usuário."""
        try:
            # Validações básicas
            if len(username) < 3:
                return {'success': False, 'error': 'Nome de usuário deve ter pelo menos 3 caracteres'}
            
            if len(password) < 6:
                return {'success': False, 'error': 'Senha deve ter pelo menos 6 caracteres'}
            
            if '@' not in email:
                return {'success': False, 'error': 'Email inválido'}
            
            # Verificar se usuário já existe
            existing_user = self.memory.get_user_by_username(username)
            if existing_user:
                return {'success': False, 'error': 'Nome de usuário já existe'}
            
            # Verificar se email já existe
            try:
                existing_email = self.memory.get_user_by_email(email)
                if existing_email:
                    return {'success': False, 'error': 'Email já cadastrado'}
            except AttributeError:
                # Método não implementado, continuar sem validação de email
                pass
            except Exception as e:
                logging.warning(f"Erro ao verificar email duplicado: {e}")
                # Continuar sem validação para não bloquear registro
            
            # Criar hash da senha
            password_hash = self.hash_password(password)
            
            # Criar usuário
            user_id = self.memory.create_user(username, email, password_hash)
            try:
                workspace_root = self.memory.ensure_user_workspace(user_id, None, username=username)
            except AttributeError:
                workspace_root = None
            except Exception as workspace_error:
                logging.error(f"Erro ao preparar workspace para novo usuário {username}: {workspace_error}")
                workspace_root = None

            logging.info(f"Usuário registrado: {username} (ID: {user_id})")
            return {
                'success': True,
                'user_id': user_id,
                'username': username,
                'workspace_root': workspace_root
            }
            
        except Exception as e:
            logging.error(f"Erro no registro: {e}")
            return {'success': False, 'error': 'Erro interno do servidor'}
    
    def login_user(self, username: str, password: str) -> dict:
        """Realiza login do usuário."""
        try:
            user = self.memory.get_user_by_username(username)
            
            if not user:
                return {'success': False, 'error': 'Usuário não encontrado'}
            
            if not user['is_active']:
                return {'success': False, 'error': 'Conta desativada'}
            
            if not self.verify_password(password, user['password_hash']):
                return {'success': False, 'error': 'Senha incorreta'}

            # Atualizar último login
            self.memory.update_last_login(user['id'])

            # Garantir que o usuário possua workspace dedicado
            try:
                workspace_root = self.memory.ensure_user_workspace(user['id'], user.get('workspace_root'), username=user['username'])
            except AttributeError:
                workspace_root = user.get('workspace_root')
            except Exception as workspace_error:
                logging.error(f"Erro ao garantir workspace do usuário {user['id']}: {workspace_error}")
                workspace_root = user.get('workspace_root')

            user['workspace_root'] = workspace_root

            # Criar sessão
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['logged_in'] = True
            session['workspace_root'] = user.get('workspace_root')

            logging.info(f"Login realizado: {username} (ID: {user['id']})")
            return {
                'success': True, 
                'user_id': user['id'], 
                'username': user['username'],
                'workspace_root': user.get('workspace_root')
            }
            
        except Exception as e:
            logging.error(f"Erro no login: {e}")
            return {'success': False, 'error': 'Erro interno do servidor'}
    
    def logout_user(self):
        """Realiza logout do usuário."""
        if 'username' in session:
            logging.info(f"Logout realizado: {session['username']}")
        
        session.clear()
        return {'success': True}

    def get_current_user(self) -> dict:
        """Retorna dados do usuário atual."""
        if not session.get('logged_in'):
            return None

        return {
            'user_id': session.get('user_id'),
            'username': session.get('username'),
            'workspace_root': session.get('workspace_root'),
            'logged_in': True
        }

def require_login(f):
    """Decorator para exigir login."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            if request.is_json:
                return jsonify({'error': 'Login necessário', 'redirect': '/login'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
