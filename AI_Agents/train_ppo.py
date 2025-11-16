# This script is used to train a Proximal Policy Optimization (PPO) agent for the MegaMiner game.
# It uses the Stable Baselines3 library for the PPO implementation and PettingZoo for the environment.
# The script can be run from the command line with various arguments to control the training process.

import os
import time
import torch
import argparse
from pathlib import Path
import supersuit as ss
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback, EvalCallback, CallbackList
from stable_baselines3.common.vec_env import VecMonitor
from pettingzoo.utils.conversions import aec_to_parallel

# Add the backend directory to the Python path if it's not already.
# This is necessary to ensure that the MegaMinerEnv can be imported correctly.
try:
    import MegaMinerEnv
except ImportError:
    import sys
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from AI_Agents import MegaMinerEnv

class TimeLimitCallback(BaseCallback):
    """
    A custom callback that stops training after a specified time limit.
    This is useful for running the training for a fixed amount of time, for example, on a schedule.
    """
    def __init__(self, max_time: int, verbose: int = 0):
        """
        Initializes the callback.
        :param max_time: The maximum time in seconds to train for.
        :param verbose: The verbosity level.
        """
        super(TimeLimitCallback, self).__init__(verbose)
        self.start_time = time.time()
        self.max_time = max_time

    def _on_step(self) -> bool:
        """
        This method will be called by the model after each call to `env.step()`.
        It checks if the elapsed time has exceeded the maximum time.
        :return: (bool) If the callback returns False, training is aborted early.
        """
        elapsed_time = time.time() - self.start_time
        if elapsed_time > self.max_time:
            if self.verbose > 0:
                print(f"Stopping training as time limit of {self.max_time} seconds reached.")
            return False
        return True

def main(args):
    """
    Main function to set up and run the PPO training.
    This function handles everything from setting up the environment to training and saving the model.
    """
    # --- 0. Configure Logging ---
    # Enable or disable logging from the game engine. This can be useful for debugging.
    if args.enable_logging:
        os.environ["MEGAMINER_LOGGING"] = "ON"
    
    # --- 1. Set Device ---
    # Set the device for training. It will use a CUDA-enabled GPU if available, otherwise an Apple Silicon GPU (MPS),
    # and will fall back to the CPU if neither is available.
    if torch.cuda.is_available():
        device = "cuda"
        print("Using CUDA (NVIDIA GPU) for training.")
    elif torch.backends.mps.is_available():
        device = "mps"
        print("Using MPS (Apple Silicon GPU) for training.")
    else:
        device = "cpu"
        print("Neither CUDA nor MPS available, using CPU for training.")

    # --- 2. Setup Environment ---
    # Create the MegaMiner environment. The map file can be specified as a command-line argument.
    map_file = str(Path(__file__).resolve().parent.parent / 'maps' / args.map_path)
    env = MegaMinerEnv.env(map_path=map_file)
    # Convert the AEC (Agent-Environment-Cycle) environment to a parallel environment.
    # This is required for compatibility with Stable Baselines3.
    env = aec_to_parallel(env)

    # --- 3. Wrap Environment for SB3 ---
    # Wrap the PettingZoo environment to be compatible with Stable Baselines3.
    # This involves vectorizing the environment and concatenating multiple environments if needed.
    env = ss.pettingzoo_env_to_vec_env_v1(env)
    env = ss.concat_vec_envs_v1(env, num_vec_envs=1, num_cpus=1, base_class="stable_baselines3")
    
    # --- 4. Setup PPO Model ---
    # Define the directories for saving logs and models.
    log_dir = "training/logs/"
    os.makedirs(log_dir, exist_ok=True)
    model_dir = "training/models/"
    os.makedirs(model_dir, exist_ok=True)
    
    # Path to the best model. This is used to continue training from a previous session.
    best_model_path = os.path.join(model_dir, "best_model", "best_model.zip")

    # If a pre-trained model exists, load it to continue training.
    # Otherwise, create a new PPO model.
    if os.path.exists(best_model_path):
        print("--- Loading existing model and continuing training ---")
        model = PPO.load(best_model_path, env=env, tensorboard_log=log_dir, device=device)
        # Reset the logger to continue logging without resetting the number of timesteps.
        from stable_baselines3.common import utils
        model.set_logger(utils.configure_logger(verbose=1, tensorboard_log=log_dir, reset_num_timesteps=False))
    else:
        print("--- No existing model found, starting new training ---")
        # Create a new PPO model with the specified hyperparameters.
        model = PPO(
            "MlpPolicy", # Use the Multi-Layer Perceptron policy.
            env,
            verbose=1,
            tensorboard_log=log_dir,
            n_steps=2048,
            batch_size=64,
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            ent_coef=0.01,
            device=device,  # Use the selected device (cuda, mps, or cpu).
        )

    # --- 5. Setup Callbacks ---
    # Set up callbacks to be used during training.
    # Time limit callback to stop training after a certain amount of time.
    max_training_time_seconds = args.train_minutes * 60
    time_callback = TimeLimitCallback(max_time=max_training_time_seconds, verbose=1)

    # Evaluation callback to evaluate the model periodically and save the best one.
    eval_env = MegaMinerEnv.env(map_path=map_file)
    eval_env = aec_to_parallel(eval_env)
    eval_env = ss.pettingzoo_env_to_vec_env_v1(eval_env)
    eval_env = ss.concat_vec_envs_v1(eval_env, num_vec_envs=1, num_cpus=1, base_class="stable_baselines3")

    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=os.path.join(model_dir, "best_model"),
        log_path=f"{log_dir}/eval",
        eval_freq=10000,
        deterministic=True,
        render=False
    )
    
    # Combine the callbacks into a single list.
    callback_list = CallbackList([eval_callback, time_callback])

    # --- 6. Train the Model ---
    # Start training the model. The total number of timesteps is set to a large number,
    # so the training will be stopped by the time limit callback.
    print(f"--- Starting PPO Training for {args.train_minutes} minutes ---")
    model.learn(total_timesteps=10_000_000, callback=callback_list)
    print("--- Finished Training ---")

    # --- 7. Save the Final Model ---
    # Save the final model after training is complete.
    final_model_path = f"{model_dir}/ppo_megaminer_final"
    model.save(final_model_path)
    print(f"Final model saved to {final_model_path}")
    print(f"Best performing model saved in {model_dir}/best_model/")

if __name__ == '__main__':
    # --- Argument Parser ---
    # Set up the argument parser to allow for command-line configuration of the training script.
    parser = argparse.ArgumentParser()
    parser.add_argument("--enable-logging", action="store_true", help="Enable game engine logging during training.")
    parser.add_argument("--map-path", type=str, default="map0.json", help="Specify the map file to use for training (e.g., 'map0.json').")
    parser.add_argument("--train-minutes", type=int, default=20, help="Specify the number of minutes to train the PPO agent.")
    args = parser.parse_args()
    main(args)