"""
Motor de análise avançada com IA para métricas complexas.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Importações opcionais para visualização e ML
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    plt = None
    sns = None
    PLOTTING_AVAILABLE = False
    print("Aviso: matplotlib/seaborn não disponível. Gráficos desabilitados.")

try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    from sklearn.cluster import KMeans
    from sklearn.ensemble import IsolationForest
    ML_AVAILABLE = True
except ImportError:
    StandardScaler = PCA = KMeans = IsolationForest = None
    ML_AVAILABLE = False
    print("Aviso: scikit-learn não disponível. Análises ML desabilitadas.")

from ..core.gemini_client import GeminiClient
from ..database.database_manager import DatabaseManager


class AnalyticsEngine:
    """Motor de análises avançadas com IA."""
    
    def __init__(self, gemini_client: GeminiClient, db_manager: DatabaseManager):
        self.gemini_client = gemini_client
        self.db_manager = db_manager
        self.models = {}
        self.cache = {}
        
    async def analyze_with_ai(self, query: str, data: pd.DataFrame) -> Dict[str, Any]:
        """Análise avançada usando IA."""
        # Prepara contexto
        context = self._prepare_data_context(data)
        
        # Identifica tipo de análise
        analysis_type = await self._identify_analysis_type(query)
        
        if analysis_type == 'prediction':
            return await self._predictive_analysis(query, data, context)
        elif analysis_type == 'clustering':
            return await self._clustering_analysis(query, data, context)
        elif analysis_type == 'anomaly':
            return await self._anomaly_detection(query, data, context)
        elif analysis_type == 'correlation':
            return await self._correlation_analysis(query, data, context)
        elif analysis_type == 'trend':
            return await self._trend_analysis(query, data, context)
        else:
            return await self._general_analysis(query, data, context)
    
    def _prepare_data_context(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Prepara contexto dos dados para análise."""
        context = {
            'shape': data.shape,
            'columns': list(data.columns),
            'dtypes': data.dtypes.to_dict(),
            'missing': data.isnull().sum().to_dict(),
            'numeric_summary': {}
        }
        
        # Resumo de colunas numéricas
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            context['numeric_summary'][col] = {
                'mean': float(data[col].mean()),
                'std': float(data[col].std()),
                'min': float(data[col].min()),
                'max': float(data[col].max()),
                'median': float(data[col].median())
            }
        
        return context
    
    async def _identify_analysis_type(self, query: str) -> str:
        """Identifica tipo de análise pela consulta."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['previsão', 'prever', 'futuro', 'projeção']):
            return 'prediction'
        elif any(word in query_lower for word in ['grupo', 'segmento', 'cluster', 'classificar']):
            return 'clustering'
        elif any(word in query_lower for word in ['anomalia', 'outlier', 'estranho', 'suspeito']):
            return 'anomaly'
        elif any(word in query_lower for word in ['correlação', 'relação', 'influencia']):
            return 'correlation'
        elif any(word in query_lower for word in ['tendência', 'evolução', 'crescimento']):
            return 'trend'
        else:
            return 'general'
    
    async def _predictive_analysis(self, query: str, data: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, Any]:
        """Análise preditiva com IA."""
        try:
            # Prepara dados para previsão
            numeric_data = data.select_dtypes(include=[np.number])
            
            if numeric_data.empty:
                return {
                    'success': False,
                    'error': 'Nenhuma coluna numérica encontrada para análise preditiva'
                }
            
            # Identifica variável alvo
            target_col = await self._identify_target_column(query, numeric_data.columns.tolist())
            
            if not target_col or target_col not in numeric_data.columns:
                target_col = numeric_data.columns[-1]  # Usa última coluna como padrão
            
            # Análise de tendência
            from statsmodels.tsa.seasonal import seasonal_decompose
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
            
            # Prepara série temporal
            ts_data = numeric_data[target_col].dropna()
            
            # Decomposição sazonal
            if len(ts_data) > 12:
                decomposition = seasonal_decompose(ts_data, model='additive', period=min(12, len(ts_data)//2))
                trend = decomposition.trend.dropna()
                seasonal = decomposition.seasonal.dropna()
                residual = decomposition.resid.dropna()
            else:
                trend = ts_data
                seasonal = pd.Series([0] * len(ts_data))
                residual = pd.Series([0] * len(ts_data))
            
            # Previsão com Holt-Winters
            forecast_periods = 10
            if len(ts_data) > 20:
                model = ExponentialSmoothing(ts_data, seasonal_periods=12, trend='add', seasonal='add')
                fitted_model = model.fit()
                forecast = fitted_model.forecast(forecast_periods)
            else:
                # Fallback para regressão linear simples
                from sklearn.linear_model import LinearRegression
                X = np.arange(len(ts_data)).reshape(-1, 1)
                lr = LinearRegression()
                lr.fit(X, ts_data)
                future_X = np.arange(len(ts_data), len(ts_data) + forecast_periods).reshape(-1, 1)
                forecast = pd.Series(lr.predict(future_X))
            
            # Gera visualização
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            
            # Gráfico histórico com componentes
            ax1.plot(ts_data.index, ts_data.values, label='Dados Reais', linewidth=2)
            if len(ts_data) > 12:
                ax1.plot(trend.index, trend.values, label='Tendência', linewidth=2, alpha=0.7)
            ax1.set_title(f'Análise de {target_col}')
            ax1.set_xlabel('Período')
            ax1.set_ylabel('Valor')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Gráfico de previsão
            ax2.plot(ts_data.index, ts_data.values, label='Histórico', linewidth=2)
            forecast_index = range(len(ts_data), len(ts_data) + len(forecast))
            ax2.plot(forecast_index, forecast.values, label='Previsão', linewidth=2, color='red', linestyle='--')
            ax2.fill_between(forecast_index, 
                           forecast.values * 0.9,  # Intervalo de confiança inferior
                           forecast.values * 1.1,  # Intervalo de confiança superior
                           alpha=0.2, color='red')
            ax2.set_title('Previsão Futura')
            ax2.set_xlabel('Período')
            ax2.set_ylabel('Valor')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Salva gráfico
            chart_dir = Path('.gemini_code/analytics')
            chart_dir.mkdir(parents=True, exist_ok=True)
            chart_path = chart_dir / f"prediction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(chart_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            # Gera insights com IA
            insights = await self._generate_prediction_insights({
                'target': target_col,
                'current_value': float(ts_data.iloc[-1]),
                'forecast_mean': float(forecast.mean()),
                'trend_direction': 'crescente' if float(forecast.mean()) > float(ts_data.iloc[-1]) else 'decrescente',
                'volatility': float(ts_data.std()),
                'forecast_values': forecast.tolist()
            })
            
            return {
                'success': True,
                'analysis_type': 'prediction',
                'target_variable': target_col,
                'current_value': float(ts_data.iloc[-1]),
                'forecast': {
                    'values': forecast.tolist(),
                    'mean': float(forecast.mean()),
                    'min': float(forecast.min()),
                    'max': float(forecast.max())
                },
                'trend': {
                    'direction': 'crescente' if float(forecast.mean()) > float(ts_data.iloc[-1]) else 'decrescente',
                    'strength': abs(float(forecast.mean()) - float(ts_data.iloc[-1])) / float(ts_data.iloc[-1]) * 100
                },
                'seasonality': bool(len(ts_data) > 12),
                'chart': str(chart_path),
                'insights': insights
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Erro na análise preditiva: {str(e)}'
            }
    
    async def _clustering_analysis(self, query: str, data: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, Any]:
        """Análise de clustering/segmentação."""
        if not ML_AVAILABLE:
            return {
                'success': False,
                'error': 'Análise de clustering requer scikit-learn'
            }
        
        try:
            # Prepara dados numéricos
            numeric_data = data.select_dtypes(include=[np.number]).dropna()
            
            if numeric_data.shape[1] < 2:
                return {
                    'success': False,
                    'error': 'Preciso de pelo menos 2 variáveis numéricas para clustering'
                }
            
            # Normaliza dados
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(numeric_data)
            
            # Determina número ótimo de clusters
            max_clusters = min(10, len(numeric_data) // 3)
            inertias = []
            
            for k in range(2, max_clusters + 1):
                kmeans = KMeans(n_clusters=k, random_state=42)
                kmeans.fit(scaled_data)
                inertias.append(kmeans.inertia_)
            
            # Método do cotovelo
            optimal_k = self._find_elbow(inertias) + 2  # +2 porque começamos em k=2
            
            # Aplica clustering final
            kmeans = KMeans(n_clusters=optimal_k, random_state=42)
            clusters = kmeans.fit_predict(scaled_data)
            
            # Adiciona clusters ao dataframe
            data_with_clusters = data.copy()
            data_with_clusters['cluster'] = clusters
            
            # Análise dos clusters
            cluster_profiles = []
            for i in range(optimal_k):
                cluster_data = numeric_data[clusters == i]
                profile = {
                    'cluster_id': i,
                    'size': len(cluster_data),
                    'percentage': len(cluster_data) / len(numeric_data) * 100,
                    'characteristics': {}
                }
                
                # Características médias
                for col in numeric_data.columns:
                    profile['characteristics'][col] = {
                        'mean': float(cluster_data[col].mean()),
                        'std': float(cluster_data[col].std())
                    }
                
                cluster_profiles.append(profile)
            
            # PCA para visualização
            if scaled_data.shape[1] > 2:
                pca = PCA(n_components=2)
                pca_data = pca.fit_transform(scaled_data)
            else:
                pca_data = scaled_data
            
            # Gera visualização
            plt.figure(figsize=(10, 8))
            scatter = plt.scatter(pca_data[:, 0], pca_data[:, 1], 
                                c=clusters, cmap='viridis', 
                                s=50, alpha=0.7, edgecolors='black', linewidth=0.5)
            
            # Adiciona centroides
            if scaled_data.shape[1] > 2:
                centroids_pca = pca.transform(scaler.transform(kmeans.cluster_centers_))
            else:
                centroids_pca = kmeans.cluster_centers_
            
            plt.scatter(centroids_pca[:, 0], centroids_pca[:, 1], 
                       c='red', s=200, alpha=1, edgecolors='black', 
                       linewidth=2, marker='*', label='Centroides')
            
            plt.title(f'Análise de Segmentação - {optimal_k} Clusters')
            plt.xlabel('Componente Principal 1')
            plt.ylabel('Componente Principal 2')
            plt.colorbar(scatter, label='Cluster')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Salva gráfico
            chart_dir = Path('.gemini_code/analytics')
            chart_dir.mkdir(parents=True, exist_ok=True)
            chart_path = chart_dir / f"clustering_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(chart_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            # Gera insights
            insights = await self._generate_clustering_insights(cluster_profiles)
            
            return {
                'success': True,
                'analysis_type': 'clustering',
                'num_clusters': optimal_k,
                'clusters': cluster_profiles,
                'chart': str(chart_path),
                'insights': insights,
                'recommendation': self._generate_cluster_recommendations(cluster_profiles)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Erro na análise de clustering: {str(e)}'
            }
    
    async def _anomaly_detection(self, query: str, data: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, Any]:
        """Detecção de anomalias/outliers."""
        try:
            # Prepara dados numéricos
            numeric_data = data.select_dtypes(include=[np.number]).dropna()
            
            if numeric_data.empty:
                return {
                    'success': False,
                    'error': 'Nenhuma coluna numérica para detecção de anomalias'
                }
            
            # Isolation Forest para detecção de anomalias
            iso_forest = IsolationForest(
                contamination=0.1,  # Assume 10% de anomalias
                random_state=42
            )
            
            # Treina modelo
            anomalies = iso_forest.fit_predict(numeric_data)
            anomaly_scores = iso_forest.score_samples(numeric_data)
            
            # Identifica anomalias
            anomaly_mask = anomalies == -1
            normal_mask = anomalies == 1
            
            # Estatísticas
            num_anomalies = sum(anomaly_mask)
            anomaly_percentage = num_anomalies / len(data) * 100
            
            # Análise detalhada das anomalias
            anomaly_details = []
            anomaly_indices = np.where(anomaly_mask)[0]
            
            for idx in anomaly_indices[:20]:  # Limita a 20 para performance
                row_data = numeric_data.iloc[idx]
                detail = {
                    'index': int(idx),
                    'anomaly_score': float(anomaly_scores[idx]),
                    'values': row_data.to_dict()
                }
                
                # Identifica por que é anomalia
                reasons = []
                for col in numeric_data.columns:
                    value = row_data[col]
                    col_mean = numeric_data[col].mean()
                    col_std = numeric_data[col].std()
                    
                    z_score = abs((value - col_mean) / col_std) if col_std > 0 else 0
                    if z_score > 3:
                        reasons.append(f"{col}: valor {value:.2f} está {z_score:.1f} desvios padrão da média")
                
                detail['reasons'] = reasons
                anomaly_details.append(detail)
            
            # Visualização
            fig, axes = plt.subplots(2, 1, figsize=(12, 10))
            
            # Gráfico de scores de anomalia
            ax1 = axes[0]
            x = range(len(anomaly_scores))
            colors = ['red' if a == -1 else 'blue' for a in anomalies]
            ax1.scatter(x, anomaly_scores, c=colors, alpha=0.6, s=20)
            ax1.axhline(y=np.percentile(anomaly_scores, 10), color='red', linestyle='--', 
                       label='Threshold de Anomalia')
            ax1.set_title('Scores de Anomalia')
            ax1.set_xlabel('Índice')
            ax1.set_ylabel('Score de Anomalia')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Heatmap de anomalias por variável
            ax2 = axes[1]
            if numeric_data.shape[1] > 1:
                # Calcula z-scores
                z_scores = np.abs((numeric_data - numeric_data.mean()) / numeric_data.std())
                anomaly_heatmap = z_scores[anomaly_mask]
                
                if len(anomaly_heatmap) > 0:
                    sns.heatmap(anomaly_heatmap.head(20).T, 
                               cmap='YlOrRd', 
                               cbar_kws={'label': 'Z-Score'},
                               ax=ax2)
                    ax2.set_title('Heatmap de Anomalias (Top 20)')
                    ax2.set_xlabel('Índice da Anomalia')
                    ax2.set_ylabel('Variável')
            
            plt.tight_layout()
            
            # Salva gráfico
            chart_dir = Path('.gemini_code/analytics')
            chart_dir.mkdir(parents=True, exist_ok=True)
            chart_path = chart_dir / f"anomalies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(chart_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            # Gera insights
            insights = await self._generate_anomaly_insights({
                'num_anomalies': num_anomalies,
                'percentage': anomaly_percentage,
                'top_anomalies': anomaly_details[:5]
            })
            
            return {
                'success': True,
                'analysis_type': 'anomaly_detection',
                'num_anomalies': num_anomalies,
                'anomaly_percentage': anomaly_percentage,
                'anomaly_details': anomaly_details,
                'chart': str(chart_path),
                'insights': insights,
                'recommendations': self._generate_anomaly_recommendations(anomaly_details)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Erro na detecção de anomalias: {str(e)}'
            }
    
    async def _correlation_analysis(self, query: str, data: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, Any]:
        """Análise de correlações entre variáveis."""
        try:
            # Prepara dados numéricos
            numeric_data = data.select_dtypes(include=[np.number])
            
            if numeric_data.shape[1] < 2:
                return {
                    'success': False,
                    'error': 'Preciso de pelo menos 2 variáveis numéricas para análise de correlação'
                }
            
            # Calcula matriz de correlação
            correlation_matrix = numeric_data.corr()
            
            # Identifica correlações fortes
            strong_correlations = []
            for i in range(len(correlation_matrix.columns)):
                for j in range(i+1, len(correlation_matrix.columns)):
                    corr_value = correlation_matrix.iloc[i, j]
                    if abs(corr_value) > 0.5:  # Correlação forte
                        strong_correlations.append({
                            'var1': correlation_matrix.columns[i],
                            'var2': correlation_matrix.columns[j],
                            'correlation': float(corr_value),
                            'strength': 'Forte' if abs(corr_value) > 0.7 else 'Moderada',
                            'direction': 'Positiva' if corr_value > 0 else 'Negativa'
                        })
            
            # Ordena por valor absoluto de correlação
            strong_correlations.sort(key=lambda x: abs(x['correlation']), reverse=True)
            
            # Visualização
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
            
            # Heatmap de correlação
            mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))
            sns.heatmap(correlation_matrix, 
                       mask=mask,
                       annot=True, 
                       fmt='.2f',
                       cmap='coolwarm',
                       center=0,
                       square=True,
                       linewidths=0.5,
                       cbar_kws={"shrink": 0.8},
                       ax=ax1)
            ax1.set_title('Matriz de Correlação')
            
            # Gráfico de dispersão para correlação mais forte
            if strong_correlations:
                strongest = strong_correlations[0]
                x_data = numeric_data[strongest['var1']]
                y_data = numeric_data[strongest['var2']]
                
                ax2.scatter(x_data, y_data, alpha=0.6, s=50)
                
                # Linha de tendência
                z = np.polyfit(x_data, y_data, 1)
                p = np.poly1d(z)
                ax2.plot(x_data, p(x_data), "r--", alpha=0.8, linewidth=2)
                
                ax2.set_xlabel(strongest['var1'])
                ax2.set_ylabel(strongest['var2'])
                ax2.set_title(f"Correlação: {strongest['correlation']:.3f}")
                ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Salva gráfico
            chart_dir = Path('.gemini_code/analytics')
            chart_dir.mkdir(parents=True, exist_ok=True)
            chart_path = chart_dir / f"correlation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(chart_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            # Análise de causalidade potencial
            causality_analysis = await self._analyze_potential_causality(strong_correlations, data)
            
            # Gera insights
            insights = await self._generate_correlation_insights({
                'num_variables': len(correlation_matrix.columns),
                'strong_correlations': strong_correlations[:5],
                'causality': causality_analysis
            })
            
            return {
                'success': True,
                'analysis_type': 'correlation',
                'num_variables': len(correlation_matrix.columns),
                'strong_correlations': strong_correlations,
                'correlation_matrix': correlation_matrix.to_dict(),
                'chart': str(chart_path),
                'insights': insights,
                'causality_hints': causality_analysis
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Erro na análise de correlação: {str(e)}'
            }
    
    async def _trend_analysis(self, query: str, data: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, Any]:
        """Análise de tendências temporais."""
        try:
            # Identifica coluna temporal
            time_cols = [col for col in data.columns 
                        if 'date' in col.lower() or 'time' in col.lower() or 'data' in col.lower()]
            
            if not time_cols:
                # Tenta usar índice como tempo
                data = data.reset_index()
                time_col = 'index'
            else:
                time_col = time_cols[0]
            
            # Prepara dados numéricos
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
            if not numeric_cols:
                return {
                    'success': False,
                    'error': 'Nenhuma coluna numérica para análise de tendência'
                }
            
            # Análise para cada métrica numérica
            trend_results = {}
            
            for col in numeric_cols[:5]:  # Limita a 5 métricas
                # Calcula tendência
                values = data[col].dropna().values
                x = np.arange(len(values))
                
                # Regressão linear
                coeffs = np.polyfit(x, values, 1)
                slope = coeffs[0]
                
                # Classificação da tendência
                avg_value = np.mean(values)
                trend_strength = abs(slope) / avg_value * 100 if avg_value != 0 else 0
                
                if abs(trend_strength) < 1:
                    trend_type = 'estável'
                elif slope > 0:
                    trend_type = 'crescente'
                else:
                    trend_type = 'decrescente'
                
                # Volatilidade
                volatility = np.std(values) / np.mean(values) * 100 if np.mean(values) != 0 else 0
                
                # Detecta pontos de mudança
                change_points = self._detect_change_points(values)
                
                trend_results[col] = {
                    'trend_type': trend_type,
                    'slope': float(slope),
                    'trend_strength': float(trend_strength),
                    'volatility': float(volatility),
                    'change_points': change_points,
                    'current_value': float(values[-1]),
                    'average_value': float(np.mean(values)),
                    'min_value': float(np.min(values)),
                    'max_value': float(np.max(values))
                }
            
            # Visualização
            num_metrics = len(trend_results)
            fig, axes = plt.subplots(num_metrics, 1, figsize=(12, 4*num_metrics), squeeze=False)
            
            for idx, (col, results) in enumerate(trend_results.items()):
                ax = axes[idx, 0]
                values = data[col].dropna().values
                x = np.arange(len(values))
                
                # Plot dados originais
                ax.plot(x, values, 'b-', alpha=0.7, linewidth=1.5, label='Dados')
                
                # Linha de tendência
                trend_line = np.polyval([results['slope'], np.mean(values)], x)
                ax.plot(x, trend_line, 'r--', linewidth=2, label='Tendência')
                
                # Marca pontos de mudança
                for cp in results['change_points']:
                    ax.axvline(x=cp, color='orange', linestyle=':', alpha=0.7)
                
                # Média móvel
                window = min(10, len(values)//4)
                if window > 1:
                    moving_avg = pd.Series(values).rolling(window=window).mean()
                    ax.plot(x, moving_avg, 'g-', alpha=0.8, linewidth=2, label=f'Média Móvel ({window})')
                
                ax.set_title(f'{col} - Tendência {results["trend_type"].title()} ({results["trend_strength"]:.1f}%)')
                ax.set_xlabel('Período')
                ax.set_ylabel('Valor')
                ax.legend()
                ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Salva gráfico
            chart_dir = Path('.gemini_code/analytics')
            chart_dir.mkdir(parents=True, exist_ok=True)
            chart_path = chart_dir / f"trend_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(chart_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            # Gera insights
            insights = await self._generate_trend_insights(trend_results)
            
            return {
                'success': True,
                'analysis_type': 'trend',
                'trends': trend_results,
                'chart': str(chart_path),
                'insights': insights,
                'recommendations': self._generate_trend_recommendations(trend_results)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Erro na análise de tendência: {str(e)}'
            }
    
    def _find_elbow(self, values: List[float]) -> int:
        """Encontra o ponto de cotovelo em uma curva."""
        if len(values) < 3:
            return 0
        
        # Calcula diferenças
        diffs = [values[i] - values[i+1] for i in range(len(values)-1)]
        
        # Encontra onde a taxa de mudança diminui significativamente
        for i in range(1, len(diffs)):
            if diffs[i] < diffs[i-1] * 0.5:  # Redução de 50% na taxa
                return i
        
        return len(values) // 2
    
    def _detect_change_points(self, values: np.ndarray, threshold: float = 2.0) -> List[int]:
        """Detecta pontos de mudança significativa em uma série."""
        if len(values) < 10:
            return []
        
        change_points = []
        window = min(10, len(values) // 5)
        
        for i in range(window, len(values) - window):
            before = values[i-window:i]
            after = values[i:i+window]
            
            # Teste t para diferença de médias
            before_mean = np.mean(before)
            after_mean = np.mean(after)
            pooled_std = np.sqrt((np.std(before)**2 + np.std(after)**2) / 2)
            
            if pooled_std > 0:
                t_stat = abs(before_mean - after_mean) / (pooled_std * np.sqrt(2/window))
                if t_stat > threshold:
                    change_points.append(i)
        
        # Remove pontos muito próximos
        if change_points:
            filtered = [change_points[0]]
            for cp in change_points[1:]:
                if cp - filtered[-1] > window:
                    filtered.append(cp)
            change_points = filtered
        
        return change_points
    
    async def _identify_target_column(self, query: str, columns: List[str]) -> Optional[str]:
        """Identifica coluna alvo baseada na consulta."""
        query_lower = query.lower()
        
        # Procura por menções diretas
        for col in columns:
            if col.lower() in query_lower:
                return col
        
        # Palavras-chave comuns
        target_keywords = {
            'vendas': ['venda', 'sales', 'revenue', 'receita'],
            'usuarios': ['usuario', 'user', 'cliente', 'customer'],
            'lucro': ['lucro', 'profit', 'margem', 'margin'],
            'custo': ['custo', 'cost', 'despesa', 'expense']
        }
        
        for col in columns:
            col_lower = col.lower()
            for category, keywords in target_keywords.items():
                if any(kw in col_lower for kw in keywords):
                    if any(kw in query_lower for kw in keywords):
                        return col
        
        return None
    
    async def _analyze_potential_causality(self, correlations: List[Dict], data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analisa potencial causalidade entre variáveis correlacionadas."""
        causality_hints = []
        
        for corr in correlations[:3]:  # Top 3 correlações
            # Análise temporal básica
            var1 = corr['var1']
            var2 = corr['var2']
            
            # Verifica se uma variável tende a mudar antes da outra
            lag_correlation = self._calculate_lag_correlation(data[var1], data[var2])
            
            hint = {
                'variables': f"{var1} → {var2}",
                'correlation': corr['correlation'],
                'lag_analysis': lag_correlation,
                'potential_cause': None
            }
            
            # Heurísticas para determinar direção causal potencial
            if abs(lag_correlation['best_lag']) > 0:
                if lag_correlation['best_lag'] > 0:
                    hint['potential_cause'] = f"{var1} pode influenciar {var2}"
                else:
                    hint['potential_cause'] = f"{var2} pode influenciar {var1}"
            
            causality_hints.append(hint)
        
        return causality_hints
    
    def _calculate_lag_correlation(self, series1: pd.Series, series2: pd.Series, max_lag: int = 5) -> Dict[str, Any]:
        """Calcula correlação com diferentes lags."""
        best_corr = 0
        best_lag = 0
        
        for lag in range(-max_lag, max_lag + 1):
            if lag < 0:
                corr = series1.iloc[:lag].corr(series2.iloc[-lag:])
            elif lag > 0:
                corr = series1.iloc[lag:].corr(series2.iloc[:-lag])
            else:
                corr = series1.corr(series2)
            
            if abs(corr) > abs(best_corr):
                best_corr = corr
                best_lag = lag
        
        return {
            'best_lag': best_lag,
            'best_correlation': float(best_corr) if not np.isnan(best_corr) else 0
        }
    
    async def _generate_prediction_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """Gera insights sobre previsões."""
        prompt = f"""
        Analise estes resultados de previsão e gere 3-5 insights acionáveis:
        
        Variável: {analysis['target']}
        Valor atual: {analysis['current_value']:.2f}
        Média prevista: {analysis['forecast_mean']:.2f}
        Direção da tendência: {analysis['trend_direction']}
        Volatilidade: {analysis['volatility']:.2f}
        
        Gere insights práticos e específicos em português.
        """
        
        response = await self.gemini_client.generate_response(prompt)
        return [line.strip() for line in response.split('\n') if line.strip() and not line.startswith('#')][:5]
    
    async def _generate_clustering_insights(self, profiles: List[Dict[str, Any]]) -> List[str]:
        """Gera insights sobre clusters."""
        prompt = f"""
        Analise estes perfis de clusters e gere insights:
        
        {json.dumps(profiles[:3], indent=2)}
        
        Identifique:
        1. Características distintivas de cada grupo
        2. Oportunidades de negócio
        3. Ações recomendadas
        
        Responda em português com insights práticos.
        """
        
        response = await self.gemini_client.generate_response(prompt)
        return [line.strip() for line in response.split('\n') if line.strip() and not line.startswith('#')][:5]
    
    async def _generate_anomaly_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """Gera insights sobre anomalias."""
        prompt = f"""
        Analise estas anomalias detectadas:
        
        Total de anomalias: {analysis['num_anomalies']}
        Percentual: {analysis['percentage']:.1f}%
        
        Top anomalias:
        {json.dumps(analysis['top_anomalies'][:3], indent=2)}
        
        Gere insights sobre:
        1. Possíveis causas
        2. Impacto no negócio
        3. Ações corretivas
        
        Responda em português.
        """
        
        response = await self.gemini_client.generate_response(prompt)
        return [line.strip() for line in response.split('\n') if line.strip() and not line.startswith('#')][:5]
    
    async def _generate_correlation_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """Gera insights sobre correlações."""
        prompt = f"""
        Analise estas correlações encontradas:
        
        Variáveis analisadas: {analysis['num_variables']}
        
        Correlações fortes:
        {json.dumps(analysis['strong_correlations'][:3], indent=2)}
        
        Gere insights sobre:
        1. Relações importantes descobertas
        2. Implicações para o negócio
        3. Como aproveitar essas relações
        
        Responda em português com insights práticos.
        """
        
        response = await self.gemini_client.generate_response(prompt)
        return [line.strip() for line in response.split('\n') if line.strip() and not line.startswith('#')][:5]
    
    async def _generate_trend_insights(self, trends: Dict[str, Dict[str, Any]]) -> List[str]:
        """Gera insights sobre tendências."""
        # Prepara resumo das tendências
        trend_summary = []
        for metric, data in list(trends.items())[:3]:
            trend_summary.append({
                'metric': metric,
                'trend': data['trend_type'],
                'strength': data['trend_strength'],
                'volatility': data['volatility']
            })
        
        prompt = f"""
        Analise estas tendências identificadas:
        
        {json.dumps(trend_summary, indent=2)}
        
        Gere insights sobre:
        1. Tendências mais importantes
        2. Riscos e oportunidades
        3. Ações recomendadas
        
        Responda em português com insights específicos e acionáveis.
        """
        
        response = await self.gemini_client.generate_response(prompt)
        return [line.strip() for line in response.split('\n') if line.strip() and not line.startswith('#')][:5]
    
    def _generate_cluster_recommendations(self, profiles: List[Dict[str, Any]]) -> List[str]:
        """Gera recomendações baseadas em clusters."""
        recommendations = []
        
        for profile in profiles:
            size_pct = profile['percentage']
            if size_pct > 40:
                recommendations.append(f"Cluster {profile['cluster_id']} representa {size_pct:.1f}% - foque estratégias principais aqui")
            elif size_pct < 10:
                recommendations.append(f"Cluster {profile['cluster_id']} é pequeno ({size_pct:.1f}%) - considere estratégias nichadas")
        
        return recommendations[:5]
    
    def _generate_anomaly_recommendations(self, anomalies: List[Dict[str, Any]]) -> List[str]:
        """Gera recomendações sobre anomalias."""
        recommendations = [
            "Investigue imediatamente as anomalias com score mais baixo",
            "Configure alertas automáticos para padrões similares",
            "Revise processos que podem estar gerando valores anômalos"
        ]
        
        if len(anomalies) > 10:
            recommendations.append("Alto número de anomalias - revise critérios de qualidade de dados")
        
        return recommendations
    
    def _generate_trend_recommendations(self, trends: Dict[str, Dict[str, Any]]) -> List[str]:
        """Gera recomendações baseadas em tendências."""
        recommendations = []
        
        for metric, data in trends.items():
            if data['trend_type'] == 'decrescente' and data['trend_strength'] > 5:
                recommendations.append(f"⚠️ {metric} em queda acentuada - ação urgente necessária")
            elif data['trend_type'] == 'crescente' and data['trend_strength'] > 10:
                recommendations.append(f"📈 {metric} em forte crescimento - aproveite o momento")
            
            if data['volatility'] > 30:
                recommendations.append(f"📊 {metric} muito volátil - implemente controles")
        
        return recommendations[:5]
    
    async def _general_analysis(self, query: str, data: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, Any]:
        """Análise geral quando tipo específico não é identificado."""
        # Combina múltiplas análises básicas
        results = {
            'success': True,
            'analysis_type': 'general',
            'data_summary': context,
            'basic_stats': {}
        }
        
        # Estatísticas básicas para cada coluna numérica
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            results['basic_stats'][col] = {
                'mean': float(data[col].mean()),
                'median': float(data[col].median()),
                'std': float(data[col].std()),
                'min': float(data[col].min()),
                'max': float(data[col].max()),
                'quartiles': {
                    'q1': float(data[col].quantile(0.25)),
                    'q2': float(data[col].quantile(0.50)),
                    'q3': float(data[col].quantile(0.75))
                }
            }
        
        # Gera insights gerais com IA
        prompt = f"""
        O usuário perguntou: "{query}"
        
        Dados disponíveis:
        - Shape: {context['shape']}
        - Colunas: {context['columns']}
        - Resumo numérico: {json.dumps(context['numeric_summary'], indent=2)}
        
        Forneça uma análise relevante e insights práticos em português.
        """
        
        response = await self.gemini_client.generate_response(prompt)
        results['ai_analysis'] = response
        results['insights'] = [line.strip() for line in response.split('\n') 
                              if line.strip() and not line.startswith('#')][:5]
        
        return results