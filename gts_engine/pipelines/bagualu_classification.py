from typing import List, Literal, Tuple, Type, Callable, Dict, Any
from argparse import Namespace
from enum import Enum

from gts_common.registry import PIPELINE_REGISTRY
from gts_common.pipeline_utils import load_args

from bagualu.lib.framework.base_gts_engine_interface import GtsEngineArgs, BaseGtsEngineInterface, TRAIN_MODE
from bagualu.lib.framework.classification_finetune.consts import InferenceEngineInputSample
from bagualu.entrances.text_classification import GtsEngineInterfaceClfStd
from bagualu.lib.framework.classification_finetune import BaseInferenceEngineClf


mode_to_interface: Dict[TRAIN_MODE, BaseGtsEngineInterface] = {
    TRAIN_MODE.STD: GtsEngineInterfaceClfStd()
}

@PIPELINE_REGISTRY.register(suffix=__name__) # type: ignore
def train_pipeline(args: GtsEngineArgs):
    train_mode = TRAIN_MODE(args.train_mode)
    module_factory = mode_to_interface[train_mode]
    module_factory.prepare_training(args)
    module_factory.generate_training_pipeline(args).main()
    
@PIPELINE_REGISTRY.register(suffix=__name__) # type: ignore
def prepare_inference(save_path):
    args: GtsEngineArgs = load_args(save_path) # type: ignore
    train_mode = TRAIN_MODE(args.train_mode)
    module_factory = mode_to_interface[train_mode]
    return module_factory.generate_inference_engine(args)

@PIPELINE_REGISTRY.register(suffix=__name__) # type: ignore
def inference(samples: List[Dict[str, Any]], inference_engine: BaseInferenceEngineClf):
    inf_sample_list = [InferenceEngineInputSample(text=sample["content"]) for sample in samples]
    results = inference_engine.inference(inf_sample_list)
    return results