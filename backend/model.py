import numpy as np
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.layers import Input, LSTM, RepeatVector, Dense, TimeDistributed
from tensorflow.keras.callbacks import EarlyStopping
import joblib
import os

class LSTMAutoencoder:
    def __init__(self, timesteps=10, n_features=6, latent_dim=32):
        self.timesteps = timesteps
        self.n_features = n_features
        self.latent_dim = latent_dim
        self.model = None
        self.scaler = None
        self.threshold = 0.8  # Default threshold
        
    def build_model(self):
        # Encoder
        inputs = Input(shape=(self.timesteps, self.n_features))
        encoded = LSTM(64, activation='relu', return_sequences=True)(inputs)
        encoded = LSTM(self.latent_dim, activation='relu', return_sequences=False)(encoded)
        
        # Decoder
        decoded = RepeatVector(self.timesteps)(encoded)
        decoded = LSTM(self.latent_dim, activation='relu', return_sequences=True)(decoded)
        decoded = LSTM(64, activation='relu', return_sequences=True)(decoded)
        decoded = TimeDistributed(Dense(self.n_features))(decoded)
        
        self.model = Model(inputs, decoded)
        self.model.compile(optimizer='adam', loss='mse')
        
    def fit(self, X, epochs=50, batch_size=32):
        if self.model is None:
            self.build_model()
        
        early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
        history = self.model.fit(
            X, X,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.2,
            callbacks=[early_stop],
            verbose=0
        )
        
        # Set threshold based on reconstruction error
        predictions = self.model.predict(X, verbose=0)
        mse = np.mean(np.power(X - predictions, 2), axis=(1,2))
        self.threshold = np.percentile(mse, 95)  # 95th percentile
        
    def predict_anomaly(self, data):
        if self.model is None:
            # Load pre-trained model if exists
            model_path = os.path.join('models', 'lstm_autoencoder.h5')
            if os.path.exists(model_path):
                self.model = load_model(model_path)
                self.scaler = joblib.load(os.path.join('models', 'scaler.pkl'))
            else:
                raise ValueError("Model not trained and no pre-trained model found")
        
        # Reshape for LSTM [batch_size, timesteps, features]
        data_reshaped = data.reshape(1, self.timesteps, self.n_features)
        
        # Predict
        reconstructed = self.model.predict(data_reshaped, verbose=0)
        
        # Calculate reconstruction error
        mse = np.mean(np.power(data_reshaped - reconstructed, 2))
        
        # Anomaly score (0-1)
        anomaly_score = min(mse / self.threshold, 1.0)
        
        return anomaly_score, mse, reconstructed.flatten()
    
    def save_model(self, path='models/lstm_autoencoder.h5'):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.model.save(path)
        joblib.dump(self.scaler, 'models/scaler.pkl')