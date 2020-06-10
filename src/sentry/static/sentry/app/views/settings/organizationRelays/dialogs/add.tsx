import {t} from 'app/locale';

import DialogManager from './dialogManager';

type Props = {
  onClose: () => void;
  open: NonNullable<DialogManager['props']['open']>;
};

type State = DialogManager['state'];

class Add extends DialogManager<Props, State> {
  componentDidUpdate(prevProps: Props, prevState: State) {
    super.componentDidUpdate(prevProps, prevState);
    if (prevProps.open !== this.props.open) {
      super.setErrors({});
      super.setOpen(this.props.open);
    }
  }

  getTitle() {
    return t('Add relay');
  }
}

export default Add;
