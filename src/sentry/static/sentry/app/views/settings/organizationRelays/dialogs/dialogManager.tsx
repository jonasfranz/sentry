import React from 'react';
import omit from 'lodash/omit';
import isEqual from 'lodash/isEqual';

import {t} from 'app/locale';

import Form from './form';
import Dialog from './dialog';

type FormProps = React.ComponentProps<typeof Form>;
type Values = FormProps['values'];

type Props = {
  onClose: () => void;
  open?: boolean;
};

type State = {
  values: Values;
  requiredValues: Array<keyof Values>;
  disables: FormProps['disables'];
  errors: FormProps['errors'];
  isFormValid: boolean;
  title: string;
  open: boolean;
};

class DialogManager<
  P extends Props = Props,
  S extends State = State
> extends React.Component<P, S> {
  state: Readonly<S> = this.getDefaultState();

  componentDidMount() {
    this.handleValidateForm();
  }

  componentDidUpdate(_prevProps: Props, prevState: S) {
    if (!isEqual(prevState.values, this.state.values)) {
      this.handleValidateForm();
    }
  }

  getDefaultState(): Readonly<S> {
    return {
      values: {name: '', publicKey: '', description: ''},
      requiredValues: ['name', 'publicKey'],
      errors: {},
      disables: {},
      isFormValid: false,
      open: !!this.props.open,
      title: this.getTitle(),
    } as Readonly<S>;
  }

  setOpen(open: S['open']) {
    this.setState({open});
  }

  setErrors(errors: S['errors']) {
    this.setState({errors});
  }

  getTitle(): string {
    return '';
  }

  clearError = <F extends keyof Values>(field: F) => {
    this.setState(prevState => ({
      errors: omit(prevState.errors, field),
    }));
  };

  handleChange = <F extends keyof Values>(field: F, value: Values[F]) => {
    this.setState(prevState => ({
      values: {
        ...prevState.values,
        [field]: value,
      },
    }));
  };

  handleSave = () => {
    // implement save method
    this.props.onClose();
  };

  handleValidateForm = () => {
    const {values, requiredValues} = this.state;
    const isFormValid = requiredValues.every(requiredValue => !!values[requiredValue]);
    this.setState({isFormValid});
  };

  handleValidate = <F extends keyof Values>(field: F) => () => {
    const isFieldValueEmpty = !this.state.values[field];
    const fieldErrorAlreadyExist = this.state.errors[field];

    if (isFieldValueEmpty && fieldErrorAlreadyExist) {
      return;
    }

    if (isFieldValueEmpty && !fieldErrorAlreadyExist) {
      this.setState(prevState => ({
        errors: {
          ...prevState.errors,
          [field]: t('Field Required'),
        },
      }));
      return;
    }

    if (!isFieldValueEmpty && fieldErrorAlreadyExist) {
      this.clearError(field);
    }
  };

  renderBody(): React.ReactElement {
    // Child has to implement this
    throw new Error('Not implemented');
  }

  render() {
    const {onClose} = this.props;
    const {values, errors, title, isFormValid, open, disables} = this.state;

    return (
      <Dialog
        title={title}
        onClose={onClose}
        onSave={this.handleSave}
        disabled={!isFormValid}
        content={
          <Form
            onChange={this.handleChange}
            onValidate={this.handleValidate}
            errors={errors}
            values={values}
            disables={disables}
          />
        }
        open={open}
      />
    );
  }
}

export default DialogManager;
