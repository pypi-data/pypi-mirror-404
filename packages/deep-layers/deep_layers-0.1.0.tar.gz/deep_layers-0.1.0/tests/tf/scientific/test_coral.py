import tensorflow as tf
from deep_layers.tf.scientific.coral import CORALLayer
import pytest

@pytest.fixture
def model_config():
    # 'units' must match 'latent_dim' if the latent is added directly as a shift
    return {
        'units': 64,
        'w0': 30.0,
        'latent_dim': 64, 
        'out_dim': 64
    }

def test_instantiation(model_config):
    model = CORALLayer(**model_config)
    assert isinstance(model, tf.keras.layers.Layer)

def test_forward_shape(model_config):
    B, N, in_dim = 4, 100, 2
    model = CORALLayer(**model_config)
    coords = tf.random.normal((B, N, in_dim))
    output = model(coords)
    assert output.shape == (B, N, model_config['units'])

def test_spatial_generalization(model_config):
    in_dim = 2
    model = CORALLayer(**model_config)
    B = 2
    latent = tf.random.normal((B, model_config['latent_dim']))

    # Resolution 1
    coords_low = tf.random.normal((B, 32, in_dim))
    out_low = model([coords_low, latent])
    assert out_low.shape == (B, 32, model_config['out_dim'])

    # Resolution 2
    coords_high = tf.random.normal((B, 128, in_dim))
    out_high = model([coords_high, latent])
    assert out_high.shape == (B, 128, model_config['out_dim'])

def test_hypernetwork_modulation(model_config):
    in_dim = 2
    model = CORALLayer(**model_config)
    B, N = 1, 10
    coords = tf.random.normal((B, N, in_dim))
    
    z1 = tf.random.normal((B, model_config['latent_dim']))
    z2 = tf.random.normal((B, model_config['latent_dim']))
    
    out1 = model([coords, z1])
    out2 = model([coords, z2])
    
    diff = tf.reduce_mean(tf.abs(out1 - out2))
    assert diff > 1e-5

def test_gradients(model_config):
    in_dim = 2
    B, N = 2, 50
    model = CORALLayer(**model_config)
    
    coords = tf.random.normal((B, N, in_dim))
    latents = tf.Variable(tf.random.normal((B, model_config['latent_dim'])))
    target = tf.random.normal((B, N, model_config['out_dim']))

    with tf.GradientTape() as tape:
        tape.watch(latents)
        preds = model([coords, latents])
        loss = tf.reduce_mean(tf.square(preds - target))
    
    grads = tape.gradient(loss, model.trainable_variables + [latents])
    assert len(grads) > 1
    # Check latent gradient
    assert grads[-1] is not None
    assert tf.norm(grads[-1]) > 0.0

def test_siren_convergence(model_config):
    in_dim = 1
    model = CORALLayer(**model_config)
    optimizer = tf.keras.optimizers.Adam(learning_rate=1e-3)
    
    B, N = 1, 100
    latents = tf.random.normal((B, model_config['latent_dim']))
    coords = tf.random.uniform((B, N, in_dim), minval=-1, maxval=1)
    target = tf.sin(10.0 * coords)

    initial_loss = None

    @tf.function
    def train_step():
        with tf.GradientTape() as tape:
            out = model([coords, latents])
            loss = tf.reduce_mean(tf.square(out - target))
        grads = tape.gradient(loss, model.trainable_variables)
        optimizer.apply_gradients(zip(grads, model.trainable_variables))
        return loss

    for i in range(50):
        loss = train_step()
        if i == 0:
            initial_loss = float(loss)
    
    assert float(loss) < initial_loss
